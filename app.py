# -*- coding: utf-8 -*-
"""app.py — Mapa Ng (SPDA). Ponto de entrada do Streamlit.

Rodar::

    streamlit run app.py

Este arquivo é só o roteiro: carregar, filtrar, classificar, desenhar. Toda a
lógica está no pacote ``mapa_ng/`` — ver ``mapa_ng/__init__.py`` para o mapa
dos módulos.

Nome do pacote
--------------
``mapa_ng`` e não ``ng``: o Windows não distingue maiúsculas em nomes de
arquivo, então um pacote ``ng/`` convivendo com um script ``Ng.py`` é ambíguo
localmente e resolve para arquivos diferentes no Linux do Streamlit Cloud.
O nome mais longo elimina a colisão.
"""
from __future__ import annotations

import streamlit as st

from mapa_ng import classificacao as cls
from mapa_ng import config as cfg
from mapa_ng import dados as dd
from mapa_ng import mapa as mp
from mapa_ng import ui
from mapa_ng.estilo import aplicar as aplicar_estilo  # noqa: F401

st.set_page_config(
    layout="wide",
    page_title="Mapa Ng",
    page_icon=":material/thunderstorm:",
)
aplicar_estilo()

st.title("Mapa Ng")
st.caption(f"Densidade de descargas atmosféricas (raios/km²/ano) · {cfg.NORMA}")

# ----------------------------------------------------------------------
# 1. Dados
# ----------------------------------------------------------------------
try:
    gdf = dd.carregar_gdf()
except dd.DadosIndisponiveis as e:
    st.error(str(e))
    st.stop()

# ----------------------------------------------------------------------
# 2. Filtros (sidebar)
# ----------------------------------------------------------------------
uf_sel, cidade_sel, faixa_ng = ui.render_filtros(gdf)
df_mapa = dd.filtrar(gdf, uf_sel, cidade_sel, faixa_ng)

if df_mapa.empty:
    st.warning("Nenhum município encontrado com os filtros selecionados.")
    st.stop()

# ----------------------------------------------------------------------
# 3. Classificação — DEPOIS dos filtros, para a escala ser local
# ----------------------------------------------------------------------
df_mapa = cls.enriquecer(df_mapa)
ui.render_legenda(cls.classes_presentes(df_mapa))

# ----------------------------------------------------------------------
# 4. Saída
# ----------------------------------------------------------------------
ui.render_metricas(df_mapa)

st.pydeck_chart(
    mp.construir_deck(df_mapa, mp.zoom_para(uf_sel, cidade_sel)),
    height=cfg.ALTURA_MAPA,
    width="stretch",
)

ui.render_tabela(df_mapa)
