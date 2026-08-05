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


def aplicar() -> bool:
    """Aplica o CSS do tema. Devolve ``True`` se conseguiu, ``False`` se caiu
    no tema padrão do Streamlit."""
    try:
        from .style import apply_sidebar_style
        apply_sidebar_style()
        return True
    except Exception:
        return False
