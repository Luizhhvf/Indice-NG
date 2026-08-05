# -*- coding: utf-8 -*-
"""gerar_cache.py — regera ``data/ng_municipios_cache_2026.parquet``.

Cruza a tabela de Ng por município com a malha municipal do IBGE e grava o
resultado simplificado em parquet — o único arquivo de dados que o app lê.

Quando rodar
------------
Só quando a fonte mudar: nova tabela de Ng (revisão da NBR 5419-2) ou nova
malha do IBGE. Fora isso, o parquet versionado no repositório basta.

A malha do IBGE
---------------
``BR_Municipios_2024.shp`` tem ~286 MB e **não está no repositório**: o GitHub
recusa arquivos acima de 100 MB. Baixe de:

    https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/
    15774-malhas.html

(Malhas territoriais > Municipal > Brasil). Descompacte e aponte o caminho com
``--shp``. O shapefile precisa das colunas ``NM_MUN``, ``NM_UF`` e ``SIGLA_UF``,
e vem acompanhado dos arquivos irmãos ``.shx``, ``.dbf``, ``.prj`` e ``.cpg`` —
todos precisam estar na mesma pasta.

Uso::

    python tools/gerar_cache.py --shp caminho/BR_Municipios_2024.shp
    python tools/gerar_cache.py --shp ... --tolerancia 0.02
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite rodar como script solto (``python tools/gerar_cache.py``) sem instalar
# o pacote: coloca a raiz do repositório na frente do sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd  # noqa: E402
import pandas as pd  # noqa: E402

from mapa_ng import config as cfg  # noqa: E402

# 0.01 grau ≈ 1 km. Suficiente para o mapa nacional e responsável por levar o
# parquet de centenas de MB para ~2,7 MB. Aumentar deixa o arquivo menor e o
# contorno mais grosseiro; diminuir faz o inverso.
TOLERANCIA_PADRAO = 0.01

URL_IBGE = ("https://www.ibge.gov.br/geociencias/organizacao-do-territorio/"
            "malhas-territoriais/15774-malhas.html")


def gerar(csv: Path, shp: Path, saida: Path, tolerancia: float) -> Path:
    """Cruza CSV + shapefile e grava o parquet. Devolve o caminho gravado."""
    print(f"[1/5] Lendo Ng por município: {csv}")
    df_ng = pd.read_csv(csv)
    for coluna in ("Municipio", "UF"):
        if coluna not in df_ng.columns:
            raise SystemExit(f"ERRO: o CSV não tem a coluna '{coluna}'.")
        df_ng[coluna] = df_ng[coluna].str.strip()
    print(f"       {len(df_ng):,} linhas".replace(",", "."))

    print(f"[2/5] Lendo malha municipal (pode demorar, ~286 MB): {shp}")
    mun = gpd.read_file(shp, columns=["NM_MUN", "NM_UF", "SIGLA_UF", "geometry"])
    mun = mun.to_crs("EPSG:4326")
    print(f"       {len(mun):,} municípios".replace(",", "."))

    print(f"[3/5] Simplificando geometria (tolerância={tolerancia})")
    mun["geometry"] = mun["geometry"].simplify(tolerancia, preserve_topology=True)
    mun["NM_MUN_join"] = mun["NM_MUN"].str.strip()

    print("[4/5] Cruzando por (município, UF)")
    gdf = mun.merge(
        df_ng,
        left_on=["NM_MUN_join", "SIGLA_UF"],
        right_on=["Municipio", "UF"],
        how="inner",
    )
    gdf = gdf.rename(columns={"NM_MUN": cfg.COL_CIDADE, "NG": cfg.COL_NG})
    gdf = gdf.drop(columns=["NM_MUN_join", "Municipio", "UF"], errors="ignore")

    perdidos = len(df_ng) - len(gdf)
    if perdidos > 0:
        # Normal: o CSV tem nomes que não batem com a grafia do IBGE. Vale
        # conferir se o número saltar de uma revisão para outra.
        print(f"       aviso: {perdidos} linhas do CSV sem município correspondente")
    print(f"       {len(gdf):,} municípios cruzados".replace(",", "."))

    print(f"[5/5] Gravando {saida}")
    saida.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(saida, index=False)
    mb = saida.stat().st_size / 1024 / 1024
    print(f"       OK — {mb:.1f} MB")
    if mb > 100:
        print("       ATENÇÃO: acima de 100 MB, o GitHub vai recusar. "
              "Aumente --tolerancia.")
    return saida


def main() -> None:
    p = argparse.ArgumentParser(
        description="Regera o cache de municípios com índice Ng.",
        epilog=f"Malha municipal do IBGE: {URL_IBGE}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--shp", type=Path, required=True,
                   help="shapefile da malha municipal do IBGE (BR_Municipios_*.shp)")
    p.add_argument("--csv", type=Path, default=None,
                   help=f"CSV de Ng por município (padrão: {cfg.CSV_NG.name})")
    p.add_argument("--saida", type=Path, default=cfg.CACHE_PARQUET,
                   help="parquet de saída")
    p.add_argument("--tolerancia", type=float, default=TOLERANCIA_PADRAO,
                   help=f"simplificação da geometria em graus (padrão {TOLERANCIA_PADRAO})")
    args = p.parse_args()

    csv = args.csv or cfg.caminho_csv()
    if csv is None or not Path(csv).exists():
        raise SystemExit(f"ERRO: CSV de Ng não encontrado em {cfg.CSV_NG}")

    if not Path(args.shp).exists():
        raise SystemExit(
            f"ERRO: shapefile não encontrado em {args.shp}\n\n"
            "Ele não faz parte do repositório (~286 MB, acima do limite de\n"
            "100 MB por arquivo do GitHub). Baixe a malha municipal em:\n"
            f"  {URL_IBGE}\n"
            "e aponte o caminho com --shp."
        )

    gerar(Path(csv), Path(args.shp), Path(args.saida), args.tolerancia)


if __name__ == "__main__":
    main()
