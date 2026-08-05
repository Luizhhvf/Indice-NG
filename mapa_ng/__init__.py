# -*- coding: utf-8 -*-
"""mapa_ng — Mapa de densidade de descargas atmosféricas (índice Ng).

Consulta do índice Ng por município brasileiro, conforme ABNT NBR 5419-2:2026,
para dimensionamento de SPDA.

Organização
-----------
::

    config.py         caminhos, colunas, paleta, zooms — tudo que é constante
    dados.py          carrega o cache .parquet e aplica filtros
    classificacao.py  faixas dinâmicas de Ng e cores derivadas
    mapa.py           monta o deck PyDeck
    ui.py             sidebar, métricas, legenda, tabela
    estilo/           CSS do tema, fundo em ondas e logo

O ponto de entrada é ``app.py``, na raiz — é ele que o Streamlit executa.

Dado
----
O app depende de um único arquivo: ``data/ng_municipios_cache_2026.parquet``
(~2,7 MB), com os municípios já cruzados com o Ng. A malha do IBGE (~286 MB)
não faz parte do repositório; serve apenas para regerar esse cache, via
``tools/gerar_cache.py``.

Nenhum módulo acessa rede, banco de dados ou serviço externo. Clonar o
repositório e instalar o ``requirements.txt`` é tudo que o app precisa.
"""

__version__ = "1.0.0"
__all__ = ["config", "dados", "classificacao", "mapa", "ui", "estilo"]
