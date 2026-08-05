# -*- coding: utf-8 -*-
"""mapa.py — construção do deck PyDeck.

Uma única camada ``GeoJsonLayer`` com os polígonos municipais, pintada pela
coluna ``cor`` que o módulo :mod:`mapa_ng.classificacao` produz.

Peso do payload
---------------
Todo vértice viaja até o navegador dentro do JSON do deck, e o deck.gl desenha
o basemap antes de receber os dados — então numa rede lenta o mapa aparece sem
as cores até o download terminar. Por isso a geometria é simplificada conforme
o zoom, em :func:`simplificar_para_zoom`. Ver ``config.TOLERANCIA_POR_ZOOM``.
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


def nivel_de(uf: str, cidade: str) -> str:
    """Nível do recorte: ``"cidade"``, ``"uf"`` ou ``"brasil"``."""
    if cidade != "Todas":
        return "cidade"
    if uf != "Todos":
        return "uf"
    return "brasil"


def zoom_para(uf: str, cidade: str) -> float:
    """Zoom conforme o nível do filtro: cidade > estado > país."""
    return {
        "cidade": cfg.ZOOM_CIDADE,
        "uf": cfg.ZOOM_UF,
        "brasil": cfg.ZOOM_BRASIL,
    }[nivel_de(uf, cidade)]


def simplificar_para_zoom(gdf: gpd.GeoDataFrame, nivel: str) -> gpd.GeoDataFrame:
    """Reduz os vértices ao que é visível no zoom correspondente.

    ``preserve_topology=True`` garante que nenhum polígono degenere nem crie
    auto-interseção — o município continua existindo, só com menos pontos.

    A simplificação é puramente visual: não altera contagem de municípios, nem
    valores de Ng, nem a classificação. Só o desenho fica mais grosso do que a
    tela consegue mostrar de qualquer forma.
    """
    tolerancia = cfg.TOLERANCIA_POR_ZOOM.get(nivel)
    if not tolerancia or gdf.empty:
        return gdf
    saida = gdf.copy()
    saida["geometry"] = saida["geometry"].simplify(tolerancia, preserve_topology=True)
    return saida


# Sentinela para distinguir "não informou estilo" de "informou None".
# ``None`` é um valor legítimo — significa "sem basemap" — então não pode ser
# usado como padrão do argumento.
_ESTILO_PADRAO = object()


def construir_deck(gdf: gpd.GeoDataFrame, zoom: float,
                   nivel: str | None = None,
                   map_style: Any = _ESTILO_PADRAO) -> pdk.Deck:
    """Monta o ``pdk.Deck`` pronto para ``st.pydeck_chart``.

    Args:
        gdf: recorte já filtrado e com as colunas de classe e cor.
        zoom: nível de zoom inicial.
        nivel: ``"brasil"``, ``"uf"`` ou ``"cidade"``. Quando informado, a
            geometria é simplificada para o orçamento daquele zoom. ``None``
            mantém o detalhe original.
        map_style: URL do estilo de basemap, ou ``None`` para não usar basemap
            nenhum. Omitido, usa ``config.MAP_STYLE``.

    ``pickable=True`` habilita o tooltip ao passar o mouse; os campos entre
    chaves são resolvidos pelo PyDeck contra as colunas do GeoDataFrame.
    """
    if nivel is not None:
        gdf = simplificar_para_zoom(gdf, nivel)

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

    estilo = cfg.MAP_STYLE if map_style is _ESTILO_PADRAO else map_style

    return pdk.Deck(
        layers=[camada],
        initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=zoom, pitch=0),
        map_style=estilo,
        tooltip=cast(Any, tooltip),
    )
