# -*- coding: utf-8 -*-
"""config.py — caminhos, constantes e paleta do Mapa Ng.

Tudo que o app precisa localizar ou colorir está declarado AQUI. Nenhum outro
módulo do pacote monta caminho na mão.

Caminhos
--------
Todos são relativos à raiz do repositório. O projeto é autossuficiente: não
depende de rede, servidor de arquivos, banco de dados nem variável de
ambiente. Clonar e rodar tem que bastar — no computador de casa, no laboratório
ou no Streamlit Cloud.
"""
from pathlib import Path

# ----------------------------------------------------------------------
# Raízes
# ----------------------------------------------------------------------
PACOTE = Path(__file__).resolve().parent          # <repo>/ng
RAIZ = PACOTE.parent                              # <repo>
DADOS = RAIZ / "data"

# ----------------------------------------------------------------------
# Dados
# ----------------------------------------------------------------------
# Cache pronto: municípios já cruzados com o Ng, geometria simplificada,
# EPSG:4326. É o ÚNICO arquivo que o app precisa para desenhar o mapa.
CACHE_PARQUET = DADOS / "ng_municipios_cache_2026.parquet"

# Fonte tabular do Ng (Municipio, UF, NG) — usada só para regerar o cache.
CSV_NG = DADOS / "ng_municipios.csv"


def _existe(caminho: Path) -> Path | None:
    """Devolve o caminho se ele existir, senão ``None``."""
    try:
        return caminho if caminho.exists() else None
    except OSError:
        return None


def caminho_cache() -> Path | None:
    """Parquet com os municípios e o Ng, ou ``None`` se não estiver no repo."""
    return _existe(CACHE_PARQUET)


def caminho_csv() -> Path | None:
    """CSV de Ng por município, ou ``None``."""
    return _existe(CSV_NG)


# ----------------------------------------------------------------------
# Colunas esperadas no cache
# ----------------------------------------------------------------------
COL_CIDADE = "Cidade"
COL_UF = "SIGLA_UF"
COL_UF_NOME = "NM_UF"
COL_NG = "Dens_km2_ano"
COL_CLASSE = "Ng_classe"
COL_COR = "cor"

COLUNAS_OBRIGATORIAS = [COL_CIDADE, COL_UF, COL_NG, "geometry"]

# ----------------------------------------------------------------------
# Classificação e paleta
# ----------------------------------------------------------------------
LABELS_NG = [
    "Muito baixo (mínimo local)",
    "Baixo",
    "Médio",
    "Alto",
    "Muito alto (máximo local)",
]

# RGBA 0-255. A escala vai do azul marinho (pouca incidência) ao amarelo puro
# (muita), passando por um verde acinzentado neutro no meio.
CORES_NG = {
    "Muito baixo (mínimo local)": [20, 55, 125, 160],
    "Baixo":                      [70, 115, 175, 170],
    "Médio":                      [140, 165, 140, 180],
    "Alto":                       [220, 200, 70, 190],
    "Muito alto (máximo local)":  [255, 235, 0, 200],
}
COR_SEM_CLASSE = [120, 120, 120, 140]

# ----------------------------------------------------------------------
# Mapa
# ----------------------------------------------------------------------
MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
CENTRO_BRASIL = (-15.78, -47.92)  # (lat, lon) — Brasília, usado se não houver dados
ZOOM_CIDADE = 10.0
ZOOM_UF = 5.5
ZOOM_BRASIL = 3.5
ALTURA_MAPA = 800

# Texto do rodapé/subtítulo — a norma de referência do índice Ng.
NORMA = "ABNT NBR 5419-2:2026"
AJUDA_NG = (
    "O índice Ng é a densidade média anual de descargas atmosféricas "
    "(raios) nuvem-solo por km² por ano. As cores se adaptam dinamicamente "
    "com base nos limites mínimo e máximo da região filtrada."
)
