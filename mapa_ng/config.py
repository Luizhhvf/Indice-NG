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
# Basemap externo (CDN da Carto). Se a rede do usuário bloquear esse domínio,
# o mapa.py cai para MAP_STYLE_FALLBACK — melhor um mapa sem fundo do que uma
# tela preta.
MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

# None = sem basemap algum. Os polígonos são desenhados sobre fundo liso, sem
# nenhuma requisição externa. Atenção: os atalhos do pydeck ("dark", "light")
# NÃO servem aqui — eles resolvem para a mesma URL da Carto e manteriam o
# problema. Só None realmente elimina a dependência de rede.
MAP_STYLE_FALLBACK = None

CENTRO_BRASIL = (-15.78, -47.92)  # (lat, lon) — Brasília, usado se não houver dados
ZOOM_CIDADE = 10.0
ZOOM_UF = 5.5
ZOOM_BRASIL = 3.5
ALTURA_MAPA = 800

# ----------------------------------------------------------------------
# Orçamento de detalhe geométrico
# ----------------------------------------------------------------------
# Todo vértice do polígono viaja até o navegador dentro do JSON do deck. Com os
# 5.488 municípios em detalhe cheio isso dá ~17 MB — 0,7 s numa fibra, mais de
# 45 s num 4G fraco. Como o deck desenha o basemap antes de receber os dados,
# numa rede lenta o mapa aparece sem as cores.
#
# A saída é simplificar conforme o zoom. Na visão nacional (zoom 3.5) um pixel
# da tela cobre cerca de 0,04°, então vértices mais finos que isso são detalhe
# que ninguém enxerga. Simplificar em 0,05° é visualmente idêntico e derruba o
# payload para ~5,9 MB.
#
# Quanto mais fechado o recorte, menos municípios sobram e mais detalhe cabe:
# um estado inteiro dá ~2 MB, uma cidade dá 4 KB. Por isso a cidade não é
# simplificada — o custo já é irrisório e o contorno importa naquele zoom.
#
# Valores em graus decimais. None = sem simplificação.
TOLERANCIA_POR_ZOOM = {
    "brasil": 0.05,   # ~5 km  — 1 pixel no zoom 3.5
    "uf":     0.01,   # ~1 km  — 1 pixel no zoom 5.5
    "cidade": None,   # detalhe original
}

# Texto do rodapé/subtítulo — a norma de referência do índice Ng.
NORMA = "ABNT NBR 5419-2:2026"
AJUDA_NG = (
    "O índice Ng é a densidade média anual de descargas atmosféricas "
    "(raios) nuvem-solo por km² por ano. As cores se adaptam dinamicamente "
    "com base nos limites mínimo e máximo da região filtrada."
)
