# -*- coding: utf-8 -*-
"""estilo — identidade visual do app.

O CSS (fundo em ondas, cards translúcidos, logo no rodapé da sidebar) mora em
:mod:`ng.estilo.style`, junto com ``fundo.html`` e ``logo-uff.png``. Tudo local:
o projeto não depende de rede nem de servidor de arquivos.

``aplicar()`` nunca levanta exceção. Estilo é enfeite; um app sem enfeite ainda
responde a pergunta de quem abriu. Se o CSS falhar, o tema base declarado em
``.streamlit/config.toml`` assume.
"""
from __future__ import annotations

import streamlit as st


def aplicar() -> bool:
    """Aplica o CSS do tema. Devolve ``True`` se conseguiu, ``False`` se não.

    Escape de diagnóstico: abrir a URL com ``?estilo=off`` pula o CSS por
    completo e o app roda só com o tema do ``.streamlit/config.toml``.

    Serve para separar problema de estilo de problema de dado sem precisar de
    console do navegador — útil justamente em celular e tablet, onde não dá
    para inspecionar. Se algo aparece com ``?estilo=off`` e some sem ele, o
    culpado é o CSS.
    """
    try:
        if st.query_params.get("estilo") == "off":
            return False
    except Exception:
        pass  # versões antigas do Streamlit não têm query_params

    try:
        from .style import apply_sidebar_style
        apply_sidebar_style()
        return True
    except Exception:
        return False
