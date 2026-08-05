# -*- coding: utf-8 -*-
"""dados.py — carregamento do GeoDataFrame de municípios com índice Ng.

O app lê UM arquivo: ``data/ng_municipios_cache_2026.parquet``. Ele já traz os
5.488 municípios cruzados com o Ng, geometria simplificada e CRS EPSG:4326 —
pronto para o PyDeck desenhar.

Por que não ler o shapefile aqui
--------------------------------
A malha municipal do IBGE (``BR_Municipios_2024.shp``) tem ~286 MB. Ela é
necessária apenas para *construir* o cache, o que acontece uma vez por revisão
da fonte, offline, via ``tools/gerar_cache.py``. Manter essa leitura fora do
app deixa o repositório com ~3 MB (viável no GitHub, que rejeita arquivos acima
de 100 MB) e o boot no Streamlit Cloud quase instantâneo.
"""
from __future__ import annotations

import geopandas as gpd
import streamlit as st

from . import config as cfg


class DadosIndisponiveis(RuntimeError):
    """Nenhuma fonte de dados foi encontrada — nem local, nem na rede."""


@st.cache_data(show_spinner="Carregando dados de Ng…")
def carregar_gdf() -> gpd.GeoDataFrame:
    """Devolve o GeoDataFrame de municípios com Ng.

    Lê ``data/ng_municipios_cache_2026.parquet``. O resultado fica no cache do
    Streamlit, então o disco é lido uma vez por sessão do servidor.

    Raises:
        DadosIndisponiveis: se o cache não for encontrado. A mensagem diz como
            regerar, em vez de deixar um traceback de arquivo não encontrado.
    """
    caminho = cfg.caminho_cache()
    if caminho is None:
        raise DadosIndisponiveis(
            f"Cache de dados não encontrado.\n\n"
            f"Esperado em: {cfg.CACHE_PARQUET}\n\n"
            f"Para regerar (precisa da malha municipal do IBGE):\n"
            f"    python tools/gerar_cache.py --shp BR_Municipios_2024.shp"
        )

    gdf = gpd.read_parquet(caminho)

    faltando = [c for c in cfg.COLUNAS_OBRIGATORIAS if c not in gdf.columns]
    if faltando:
        raise DadosIndisponiveis(
            f"O cache em {caminho.name} não tem as colunas {faltando}. "
            f"Regere com: python tools/gerar_cache.py --shp <malha do IBGE>"
        )

    # O PyDeck espera lat/lon em graus; garante o CRS mesmo que o parquet
    # tenha sido gravado por uma versão diferente do geopandas.
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")

    return gdf


def filtrar(gdf: gpd.GeoDataFrame, uf: str, cidade: str,
            faixa_ng: tuple[float, float]) -> gpd.GeoDataFrame:
    """Aplica os três filtros da sidebar, nesta ordem: UF, cidade, faixa de Ng.

    ``uf="Todos"`` e ``cidade="Todas"`` desativam o filtro correspondente —
    são os rótulos que a sidebar usa para "sem filtro".
    """
    df = gdf
    if uf != "Todos":
        df = df[df[cfg.COL_UF] == uf]
    if cidade != "Todas":
        df = df[df[cfg.COL_CIDADE] == cidade]
    df = df[df[cfg.COL_NG].between(faixa_ng[0], faixa_ng[1])]
    return df.copy()


def limites_ng(gdf: gpd.GeoDataFrame) -> tuple[float, float]:
    """(mínimo, máximo) de Ng, já protegido contra os dois serem iguais.

    O ``st.slider`` recusa ``min_value == max_value``. Isso acontece de verdade
    ao filtrar uma cidade só, então a margem de ±0.1 evita quebrar a sidebar.
    """
    if gdf.empty:
        return 0.0, 1.0
    minimo = float(gdf[cfg.COL_NG].min())
    maximo = float(gdf[cfg.COL_NG].max())
    if minimo == maximo:
        return max(0.0, minimo - 0.1), maximo + 0.1
    return minimo, maximo
