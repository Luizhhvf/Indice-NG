# -*- coding: utf-8 -*-
"""classificacao.py — faixas de Ng e cores derivadas.

A classificação é **dinâmica**: as cinco faixas são recalculadas sobre o
recorte que está na tela, não sobre o Brasil inteiro. Filtrar só o Ceará faz o
"Muito alto" passar a significar "muito alto para o Ceará".

A escolha é intencional. Com faixas fixas nacionais, estados de baixa
incidência apareceriam inteiramente azuis e o mapa não informaria nada sobre a
variação interna — que é justamente o que interessa a quem dimensiona SPDA em
uma região específica. O custo é que a cor não é comparável entre dois
recortes diferentes, e por isso os rótulos dizem "mínimo/máximo local".
"""
from __future__ import annotations

import pandas as pd

from . import config as cfg


def classificar_ng(series: pd.Series) -> pd.Series:
    """Divide os valores em 5 faixas por quantis (``pd.qcut``).

    Quantis, e não intervalos iguais: a distribuição de Ng é assimétrica, com
    muitos municípios em valores baixos. Cortar em intervalos iguais jogaria
    quase tudo na primeira faixa e deixaria as outras quatro quase vazias.

    Degradações previstas:

    * série com um único valor distinto -> tudo na primeira faixa;
    * distribuição concentrada demais para 5 quantis distintos -> cai para
      ``pd.cut`` (intervalos iguais), que sempre produz algum corte.
    """
    if series.nunique() <= 1:
        return pd.Series(cfg.LABELS_NG[0], index=series.index)
    try:
        return pd.qcut(series, q=5, labels=cfg.LABELS_NG, duplicates="drop")
    except (ValueError, IndexError):
        return pd.cut(series, bins=5, labels=cfg.LABELS_NG, include_lowest=True)


def cor_por_classe(classes: pd.Series) -> pd.Series:
    """Mapeia cada rótulo de faixa para o RGBA da paleta.

    Valores fora da paleta (ex.: NaN quando ``qcut`` descarta duplicatas) viram
    o cinza neutro de ``COR_SEM_CLASSE`` — visível no mapa, mas sem sugerir uma
    intensidade que não foi medida.
    """
    return classes.astype(str).map(cfg.CORES_NG).apply(
        lambda cor: cor if isinstance(cor, list) else cfg.COR_SEM_CLASSE
    )


def enriquecer(gdf, series_ng=None):
    """Acrescenta as colunas de classe e cor ao GeoDataFrame já filtrado.

    Deve rodar DEPOIS dos filtros — é o que torna a escala local. Chamar antes
    congelaria as faixas na distribuição nacional.
    """
    alvo = cfg.COL_NG if series_ng is None else series_ng
    gdf[cfg.COL_CLASSE] = classificar_ng(gdf[alvo])
    gdf[cfg.COL_COR] = cor_por_classe(gdf[cfg.COL_CLASSE])
    return gdf


def classes_presentes(gdf) -> list[str]:
    """Rótulos que realmente aparecem no recorte, na ordem da paleta.

    Serve para a legenda não listar faixas vazias — ao filtrar uma cidade só,
    mostrar as cinco cores seria enganoso.
    """
    if cfg.COL_CLASSE not in gdf.columns:
        return list(cfg.LABELS_NG)
    presentes = set(gdf[cfg.COL_CLASSE].astype(str))
    return [rotulo for rotulo in cfg.LABELS_NG if rotulo in presentes]
