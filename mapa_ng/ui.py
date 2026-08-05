# -*- coding: utf-8 -*-
"""ui.py — componentes de interface: filtros, legenda, métricas e tabela.

Cada função desenha um pedaço da tela e devolve o que o ``app.py`` precisa
para seguir. A regra do módulo: nada de regra de negócio aqui — cálculo de
faixa mora em :mod:`mapa_ng.classificacao`, filtro mora em :mod:`mapa_ng.dados`.
"""
from __future__ import annotations

import io

import geopandas as gpd
import pandas as pd
import streamlit as st

from . import config as cfg
from . import dados as dd


def render_filtros(gdf: gpd.GeoDataFrame) -> tuple[str, str, tuple[float, float]]:
    """Desenha a sidebar de filtros e devolve ``(uf, cidade, faixa_ng)``.

    Os filtros são encadeados: a lista de cidades depende da UF escolhida, e os
    limites do slider dependem do recorte já selecionado. Assim o slider sempre
    cobre exatamente a faixa que existe na seleção atual, em vez de manter uma
    escala nacional em que a cidade escolhida ocuparia um único pixel.
    """
    st.sidebar.header("Filtros")

    ufs = sorted(gdf[cfg.COL_UF].dropna().unique())
    uf_sel = st.sidebar.selectbox("Estado (UF)", options=["Todos"] + list(ufs))

    gdf_uf = gdf if uf_sel == "Todos" else gdf[gdf[cfg.COL_UF] == uf_sel]
    cidades = sorted(gdf_uf[cfg.COL_CIDADE].dropna().unique())
    cidade_sel = st.sidebar.selectbox("Cidade", options=["Todas"] + list(cidades))

    recorte = gdf_uf if cidade_sel == "Todas" else gdf_uf[gdf_uf[cfg.COL_CIDADE] == cidade_sel]
    ng_min, ng_max = dd.limites_ng(recorte)

    faixa = st.sidebar.slider(
        "Faixa de Ng (raios/km²/ano)",
        min_value=ng_min,
        max_value=ng_max,
        value=(ng_min, ng_max),
        step=0.1,
        format="%.1f",
    )
    return uf_sel, cidade_sel, faixa


def render_legenda(labels_visiveis: list[str]) -> None:
    """Quadradinhos coloridos da legenda, só das faixas presentes no recorte."""
    st.sidebar.divider()
    st.sidebar.markdown("### Legenda – Ng dinâmica", help=cfg.AJUDA_NG)

    for rotulo in labels_visiveis:
        cor = cfg.CORES_NG.get(rotulo)
        if not cor:
            continue
        rgba = f"rgba({cor[0]},{cor[1]},{cor[2]},{cor[3] / 255:.2f})"
        st.sidebar.markdown(
            f'<div style="display:flex;align-items:center;margin-bottom:4px;">'
            f'<div style="width:16px;height:16px;background:{rgba};'
            f'margin-right:8px;border-radius:3px;"></div>'
            f'<span>{rotulo}</span></div>',
            unsafe_allow_html=True,
        )


def render_metricas(gdf: gpd.GeoDataFrame) -> None:
    """Quatro métricas do recorte: contagem, mínimo, máximo e média de Ng."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pontos exibidos", f"{len(gdf):,}".replace(",", "."))
    c2.metric("Ng mínimo", f"{gdf[cfg.COL_NG].min():.2f}")
    c3.metric("Ng máximo", f"{gdf[cfg.COL_NG].max():.2f}")
    c4.metric("Ng médio", f"{gdf[cfg.COL_NG].mean():.2f}")


def _para_excel(df: pd.DataFrame) -> bytes:
    """Serializa o DataFrame em .xlsx na memória (sem tocar em disco)."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Ng")
    return buf.getvalue()


def render_tabela(gdf: gpd.GeoDataFrame) -> None:
    """Tabela do recorte dentro de um expander, com download em Excel.

    A coluna ``geometry`` fica de fora: são polígonos com milhares de vértices,
    ilegíveis numa planilha e suficientes para inviabilizar o arquivo.
    """
    with st.expander(":material/table_chart: Ver dados tabulares"):
        colunas = [c for c in (cfg.COL_CIDADE, cfg.COL_UF, cfg.COL_NG, cfg.COL_CLASSE)
                   if c in gdf.columns]
        tabela = (
            pd.DataFrame(gdf[colunas])
            .rename(columns={
                cfg.COL_NG: "Ng (raios/km²/ano)",
                cfg.COL_CLASSE: "Classe",
                cfg.COL_UF: "UF",
            })
            .sort_values("Ng (raios/km²/ano)", ascending=False)
            .reset_index(drop=True)
        )
        st.dataframe(tabela, width="stretch", height=320)
        st.download_button(
            "Baixar tabela (Excel)",
            data=_para_excel(tabela),
            file_name="Mapa Ng.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
