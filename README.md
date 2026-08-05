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
├── ng/
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

O `app.py` é só o roteiro: carregar, filtrar, classificar, desenhar. Cada
módulo de `ng/` tem uma responsabilidade única e nenhum monta caminho de
arquivo na mão — tudo passa por `config.py`.

O projeto é autossuficiente: sem rede, banco de dados, credencial ou variável
de ambiente. As dependências estão em `requirements.txt`, com limite superior
de versão (`~=`) em vez de pin exato, porque ambientes que recompilam a cada
build falham quando um patch específico sai do índice.

---

## Dados

O app lê um único arquivo: `data/ng_municipios_cache_2026.parquet` — 5.488
municípios, geometria simplificada, CRS EPSG:4326, valor de Ng por município.

Ele resulta do cruzamento de duas fontes:

| Fonte | Conteúdo | Versionada |
|---|---|---|
| `data/ng_municipios.csv` | Ng por município, NBR 5419-2:2026 | sim — 110 KB |
| `BR_Municipios_2024.shp` ([IBGE][ibge]) | malha municipal | não — 286 MB |

A malha do IBGE fica fora do repositório porque ultrapassa o limite de 100 MB
por arquivo do GitHub. Ela é insumo de construção, não de execução: o
`tools/gerar_cache.py` a consome uma vez, simplifica a geometria com tolerância
de 0,01 grau (≈ 1 km) e grava o parquet de 2,7 MB que o app efetivamente usa.
Isso mantém o repositório em ~3 MB e o boot praticamente instantâneo.

O script aceita `--shp`, `--csv`, `--saida` e `--tolerancia`; `--help` descreve
cada um. Só precisa rodar quando a tabela de Ng ou a malha do IBGE forem
revisadas.

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

---

## Limitações conhecidas

- Com **um só município** selecionado não existe dispersão para classificar, e
  ele sempre recebe o rótulo mais baixo da escala. A legenda perde sentido
  nesse recorte — o valor absoluto está na tabela e no tooltip.
- O cruzamento entre o CSV e a malha do IBGE é feito por nome de município e
  sigla de UF. Divergências de grafia entre as fontes descartam a linha
  silenciosamente; o `gerar_cache.py` reporta a contagem ao final.
