# -*- coding: utf-8 -*-
"""mapa.py — construção do deck PyDeck.

Uma única camada ``GeoJsonLayer`` com os polígonos municipais, pintada pela
coluna ``cor`` que o módulo :mod:`mapa_ng.classificacao` produz.
"""
from __future__ import annotations

from typing import Any, cast

import geopandas as gpd
import pydeck as pdk

from . import config as cfg


def centro(gdf: gpd.GeoDataFrame) -> tuple[float, float]:
    """(lat, lon) do centro da bounding box do recorte.

    Com o recorte vazio não há bounds — devolve o centro do Brasil para o mapa
    abrir em algum lugar razoável em vez de em (0, 0), no golfo da Guiné.
    """
    if gdf.empty:
        return cfg.CENTRO_BRASIL
    oeste, sul, leste, norte = gdf.total_bounds
    return (sul + norte) / 2, (oeste + leste) / 2


def zoom_para(uf: str, cidade: str) -> float:
    """Zoom conforme o nível do filtro: cidade > estado > país."""
    if cidade != "Todas":
        return cfg.ZOOM_CIDADE
    if uf != "Todos":
        return cfg.ZOOM_UF
    return cfg.ZOOM_BRASIL


def construir_deck(gdf: gpd.GeoDataFrame, zoom: float) -> pdk.Deck:
    """Monta o ``pdk.Deck`` pronto para ``st.pydeck_chart``.

    ``pickable=True`` habilita o tooltip ao passar o mouse; os campos entre
    chaves são resolvidos pelo PyDeck contra as colunas do GeoDataFrame.
    """
    lat, lon = centro(gdf)

    camada = pdk.Layer(
        "GeoJsonLayer",
        gdf,
        opacity=0.7,
        stroked=True,
        filled=True,
        extruded=False,
        get_fill_color=cfg.COL_COR,
        get_line_color=[200, 200, 200, 150],
        line_width_min_pixels=0.3,
        pickable=True,
    )

    tooltip = {
        "text": (
            "Cidade: {%s}\nUF: {%s}\nNg: {%s}\nClasse: {%s}"
            % (cfg.COL_CIDADE, cfg.COL_UF, cfg.COL_NG, cfg.COL_CLASSE)
        )
    }

    return pdk.Deck(
        layers=[camada],
        initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=zoom, pitch=0),
        map_style=cfg.MAP_STYLE,
        tooltip=cast(Any, tooltip),
    )
