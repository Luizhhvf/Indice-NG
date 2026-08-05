# Mapa Ng — SPDA

Consulta do índice **Ng** — densidade de descargas atmosféricas nuvem-solo, em
raios/km²/ano — por município brasileiro, para dimensionamento de sistemas de
proteção contra descargas atmosféricas conforme **ABNT NBR 5419-2:2026**.

Aplicação Streamlit com mapa interativo, filtro por estado, cidade e faixa de
Ng, classificação dinâmica em cinco níveis, métricas do recorte e exportação da
tabela em Excel.

---

## Arquitetura

```
.
├── app.py                    ponto de entrada — orquestra o fluxo da tela
├── requirements.txt
├── .streamlit/config.toml    tema base
├── mapa_ng/
│   ├── config.py             caminhos, colunas, paleta, zooms
│   ├── dados.py              carga do parquet e filtros
│   ├── classificacao.py      faixas dinâmicas de Ng e cores
│   ├── mapa.py               camada GeoJson e viewport do PyDeck
│   ├── ui.py                 sidebar, métricas, legenda, tabela
│   └── estilo/               CSS, fundo em ondas e logo
├── data/
│   ├── ng_municipios_cache_2026.parquet
│   └── ng_municipios.csv
└── tools/
    └── gerar_cache.py        reconstrói o parquet a partir da malha do IBGE
```
## Dados

O app lê um único arquivo: `data/ng_municipios_cache_2026.parquet` — 5.488
municípios, geometria simplificada, CRS EPSG:4326, valor de Ng por município.

Ele resulta do cruzamento de duas fontes:

| Fonte | Conteúdo | Versionada |
|---|---|---|
| `data/ng_municipios.csv` | Ng por município, NBR 5419-2:2026 | sim — 110 KB |
| `BR_Municipios_2024.shp` ([IBGE][ibge]) | malha municipal | não — 286 MB |

[ibge]: https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html

---
## Classificação dinâmica
As cinco faixas de cor são recalculadas por quantis **sobre o recorte visível**,
não sobre o Brasil inteiro. Filtrar o Ceará faz "Muito alto" passar a significar
"muito alto para o Ceará".

A escolha é deliberada. Com faixas fixas nacionais, estados de baixa incidência
apareceriam uniformemente azuis e o mapa não revelaria a variação interna — que
é justamente o que interessa a quem dimensiona SPDA numa região específica.

O custo é que a cor **não é comparável entre dois recortes diferentes**; por
isso os rótulos dizem "mínimo local" e "máximo local". Para o valor absoluto,
a tabela e o tooltip trazem o número.

Quantis em vez de intervalos de mesma largura porque a distribuição de Ng é
assimétrica: cortar em cinco intervalos iguais concentraria quase todos os
municípios na primeira faixa. Quando a distribuição é concentrada demais para
cinco quantis distintos, há degradação para `pd.cut`; com um único valor
distinto, tudo cai na primeira faixa.

