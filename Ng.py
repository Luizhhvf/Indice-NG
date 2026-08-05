import streamlit as st
import pandas as pd
import pydeck as pdk
import geopandas as gpd
import json
from pathlib import Path
from typing import Any, cast
import io
import sys
sys.path.append(r"\\servidor01\p&d$\0 - PROGRAMACAO\12 - DASHBOARD DE OBRAS\1 - PROGRAMA\0 - Dashboard\DOCFLOW")
from core.style import apply_sidebar_style # type: ignore
st.set_page_config(layout="wide", page_title="Mapa Ng", page_icon=":material/thunderstorm:")
apply_sidebar_style()

# --------------------------------------------------
# Constantes
# --------------------------------------------------
ARQUIVO_EXCEL = r"\\servidor01\p&d$\0 - PROGRAMACAO\12 - DASHBOARD DE OBRAS\3 - ELABORAÇÃO\6 - SPDA\APP SPDA\templates\ng_municipios.csv"
ARQUIVO_CSV = ARQUIVO_EXCEL
ARQUIVO_SHP   = r"\\servidor01\p&d$\0 - PROGRAMACAO\12 - DASHBOARD DE OBRAS\2 - MATERIAL DE APOIO\1 - NG(SPDA)\BR_Municipios_2024.shp"
CACHE_PARQUET = Path(r"\\servidor01\p&d$\0 - PROGRAMACAO\12 - DASHBOARD DE OBRAS\2 - MATERIAL DE APOIO\1 - NG(SPDA)\ng_municipios_cache_2026.parquet")

# Mudança nos labels para refletir a dispersão dinâmica (escala local)
LABELS_NG = ["Muito baixo (mínimo local)", "Baixo", "Médio", "Alto", "Muito alto (máximo local)"]

CORES_NG = {
    "Muito baixo (mínimo local)":  [20,   55,  125, 160],  # Azul Escuro / Marinho
    "Baixo":                       [70,  115,  175, 170],  # Azul Médio / Mineral
    "Médio":                       [140, 165,  140, 180],  # Transição (Verde Pálido / Cinza)
    "Alto":                        [220, 200,   70, 190],  # Amarelo Queimado / Ouro
    "Muito alto (máximo local)":   [255, 235,    0, 200],  # Amarelo Brilhante / Puro
}

# --------------------------------------------------
# Carregamento de dados
# --------------------------------------------------
@st.cache_data(show_spinner="Carregando dados de Ng (2026)…")
def carregar_gdf() -> gpd.GeoDataFrame:
    if CACHE_PARQUET.exists():
        return gpd.read_parquet(CACHE_PARQUET)

    # — leitura do CSV (Dados 2026) —
    df_ng = pd.read_csv(ARQUIVO_CSV)
    df_ng["Municipio"] = df_ng["Municipio"].str.strip()
    df_ng["UF"] = df_ng["UF"].str.strip()

    # — shapefile dos municípios brasileiros —
    mun = gpd.read_file(ARQUIVO_SHP, columns=["NM_MUN", "NM_UF", "SIGLA_UF", "geometry"])
    mun = mun.to_crs("EPSG:4326")
    
    # Simplificação geométrica (importante para o mapa não ficar pesado)
    mun_simpl = mun.copy()
    mun_simpl["geometry"] = mun_simpl["geometry"].simplify(0.01, preserve_topology=True)
    mun_simpl["NM_MUN_join"] = mun_simpl["NM_MUN"].str.strip()

    # — Cruzamento —
    gdf = mun_simpl.merge(
        df_ng, 
        left_on=["NM_MUN_join", "SIGLA_UF"], 
        right_on=["Municipio", "UF"], 
        how="inner"
    )

    # Padronização de colunas
    gdf.rename(columns={"NM_MUN": "Cidade", "NG": "Dens_km2_ano"}, inplace=True)
    gdf.drop(columns=["NM_MUN_join", "Municipio", "UF"], errors="ignore", inplace=True)

    try:
        gdf.to_parquet(CACHE_PARQUET, index=False)
    except Exception:
        pass 

    return gdf

# --------------------------------------------------
# Classificação Dinâmica de Ng (Alta Dispersão por Quantis)
# --------------------------------------------------
def classificar_ng_dinamico(series: pd.Series) -> pd.Series:
    if series.nunique() <= 1:
        return pd.Series(LABELS_NG[0], index=series.index)
    
    try:
        # qcut divide igualmente os dados em 5 faixas com base na amostragem atual
        return pd.qcut(series, q=5, labels=LABELS_NG, duplicates="drop")
    except Exception:
        # Fallback caso a distribuição seja muito concentrada em um único valor
        return pd.cut(series, bins=5, labels=LABELS_NG, include_lowest=True)


def cor_por_classe(classe_series: pd.Series) -> pd.Series:
    return classe_series.astype(str).map(CORES_NG).apply(
        lambda x: x if isinstance(x, list) else [120, 120, 120, 140]
    )


def raio_proporcional(series: pd.Series) -> pd.Series:
    vmin, vmax = series.min(), series.max()
    if vmax > vmin:
        return ((series - vmin) / (vmax - vmin)) * 30_000 + 8_000
    return pd.Series(15_000, index=series.index)


# --------------------------------------------------
# Legenda na sidebar
# --------------------------------------------------
def render_legenda(labels_visiveis: list[str]) -> None:
    st.sidebar.markdown(
        "### Legenda – Ng Dinâmica",
        help=(
            "O índice Ng é a densidade média anual de descargas atmosféricas "
            "(raios) nuvem-solo por km² por ano. As cores se adaptam dinamicamente "
            "com base nos limites mínimo e máximo da região filtrada."
        ),
    )
    for label in labels_visiveis:
        cor = CORES_NG.get(label)
        if not cor:
            continue
        rgba = f"rgba({cor[0]},{cor[1]},{cor[2]},{cor[3]/255:.2f})"
        st.sidebar.markdown(
            f"""<div style="display:flex;align-items:center;margin-bottom:4px;">
                  <div style="width:16px;height:16px;background:{rgba};
                              margin-right:8px;border-radius:3px;"></div>
                  <span>{label}</span>
               </div>""",
            unsafe_allow_html=True,
        )


# --------------------------------------------------
# Estatísticas resumidas
# --------------------------------------------------
def render_estatisticas(df: pd.DataFrame) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pontos exibidos",  f"{len(df):,}".replace(",", "."))
    col2.metric("Ng mínimo",        f"{df['Dens_km2_ano'].min():.2f}")
    col3.metric("Ng máximo",        f"{df['Dens_km2_ano'].max():.2f}")
    col4.metric("Ng médio",         f"{df['Dens_km2_ano'].mean():.2f}")


# --------------------------------------------------
# Construção das layers PyDeck
# --------------------------------------------------
def build_deck(df_mapa: gpd.GeoDataFrame, zoom: float) -> pdk.Deck:
    if not df_mapa.empty:
        bounds = df_mapa.total_bounds
        lon_c = (bounds[0] + bounds[2]) / 2
        lat_c = (bounds[1] + bounds[3]) / 2
    else:
        lat_c, lon_c = -15.78, -47.92

    geojson_layer = pdk.Layer(
        "GeoJsonLayer",
        df_mapa,
        opacity=0.7,
        stroked=True,
        filled=True,
        extruded=False,
        get_fill_color="cor",
        get_line_color=[200, 200, 200, 150],
        line_width_min_pixels=0.3,
        pickable=True,
    )

    view = pdk.ViewState(latitude=lat_c, longitude=lon_c, zoom=zoom, pitch=0)

    return pdk.Deck(
        layers=[geojson_layer],
        initial_view_state=view,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip=cast(Any, {"text": "Cidade: {Cidade}\nUF: {SIGLA_UF}\nNg: {Dens_km2_ano}\nClasse: {Ng_classe}"}),
    )

# ==================================================
# APP PRINCIPAL
# ==================================================
st.title("Mapa Ng")
st.caption("Densidade de descargas atmosféricas (raios/km²/ano) · ABNT NBR 5419-2:2026")

gdf = carregar_gdf()

# --------------------------------------------------
# Sidebar – filtros
# --------------------------------------------------
with st.sidebar:
    st.header("Filtros")

    # Filtro por UF
    ufs = sorted(gdf["SIGLA_UF"].dropna().unique())
    uf_sel = st.selectbox("Estado (UF)", options=["Todos"] + ufs)

    gdf_uf = gdf if uf_sel == "Todos" else gdf[gdf["SIGLA_UF"] == uf_sel]
    cidades = sorted(gdf_uf["Cidade"].dropna().unique())
    cidade_sel = st.selectbox("Cidade", options=["Todas"] + cidades)

    # Cálculo dinâmico da escala do Slider baseado nas localizações
    if cidade_sel != "Todas":
        df_limites = gdf_uf[gdf_uf["Cidade"] == cidade_sel]
    else:
        df_limites = gdf_uf

    ng_dinamico_min = float(df_limites["Dens_km2_ano"].min())
    ng_dinamico_max = float(df_limites["Dens_km2_ano"].max())

    # Margem de segurança contra min/max idênticos
    if ng_dinamico_min == ng_dinamico_max:
        ng_dinamico_min = max(0.0, ng_dinamico_min - 0.1)
        ng_dinamico_max = ng_dinamico_max + 0.1

    # Filtro por faixa de Ng adaptativo
    ng_range = st.slider(
        "Faixa de Ng (raios/km²/ano)",
        min_value=ng_dinamico_min,
        max_value=ng_dinamico_max,
        value=(ng_dinamico_min, ng_dinamico_max),
        step=0.1,
        format="%.1f",
    )

    st.divider()
    render_legenda(LABELS_NG)

# --------------------------------------------------
# Aplicação dos filtros no mapa
# --------------------------------------------------
df_mapa = gdf.copy()

if uf_sel != "Todos":
    df_mapa = df_mapa[df_mapa["SIGLA_UF"] == uf_sel]

if cidade_sel != "Todas":
    df_mapa = df_mapa[df_mapa["Cidade"] == cidade_sel]

df_mapa = df_mapa[
    df_mapa["Dens_km2_ano"].between(ng_range[0], ng_range[1])
].copy()

if df_mapa.empty:
    st.warning("Nenhum ponto encontrado com os filtros selecionados.")
    st.stop()

# --------------------------------------------------
# Enriquecimento visual dinâmico (Aplicado APÓS filtros)
# --------------------------------------------------
df_mapa["Ng_classe"] = classificar_ng_dinamico(df_mapa["Dens_km2_ano"])
df_mapa["cor"]       = cor_por_classe(df_mapa["Ng_classe"])
df_mapa["raio"]      = raio_proporcional(df_mapa["Dens_km2_ano"])

# --------------------------------------------------
# Métricas resumidas
# --------------------------------------------------
render_estatisticas(df_mapa)

# --------------------------------------------------
# Zoom automático
# --------------------------------------------------
if cidade_sel != "Todas":
    zoom = 10.0
elif uf_sel != "Todos":
    zoom = 5.5
else:
    zoom = 3.5

# --------------------------------------------------
# Mapa
# --------------------------------------------------
st.pydeck_chart(build_deck(df_mapa, zoom))

# --------------------------------------------------
# Tabela de dados (expansível)
# --------------------------------------------------
with st.expander(":material/table_chart: Ver dados tabulares"):
    cols_tabela = ["Cidade", "SIGLA_UF", "Dens_km2_ano", "Ng_classe"]
    cols_tabela = [c for c in cols_tabela if c in df_mapa.columns]
    st.dataframe(
        df_mapa[cols_tabela]
        .rename(columns={"Dens_km2_ano": "Ng (raios/km²/ano)", "Ng_classe": "Classe", "SIGLA_UF": "UF"})
        .sort_values("Ng (raios/km²/ano)", ascending=False)
        .reset_index(drop=True),
        width='stretch',
        height=320,
    )
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        df_mapa.to_excel(w, index=False, sheet_name='Atividades')
    st.download_button(
        "Tabela NG (Excel)",
        data=buf.getvalue(),
        file_name="Tabela NG (Excel).xlsx",
        mime="application/vnd.ms-excel",
        width='stretch'
    )
