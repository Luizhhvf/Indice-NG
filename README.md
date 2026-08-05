# Mapa Ng — SPDA

Consulta do índice **Ng** (densidade de descargas atmosféricas, em raios/km²/ano)
por município brasileiro, para dimensionamento de SPDA conforme
**ABNT NBR 5419-2:2026**.

Mapa interativo com filtro por estado, cidade e faixa de Ng, classificação
dinâmica em cinco níveis, métricas do recorte e exportação da tabela em Excel.

---

## Rodando localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Não precisa de rede, banco de dados nem credencial. O dado necessário
(`data/ng_municipios_cache_2026.parquet`, 2,7 MB) está no repositório.

## Publicando no Streamlit Cloud

1. Suba este diretório como repositório no GitHub.
2. Em [share.streamlit.io](https://share.streamlit.io), aponte para o repo.
3. Main file path: `app.py`.

O `requirements.txt` cobre todas as dependências e não há segredo a configurar.

---

## Estrutura

```
1 - NG(SPDA)/
├── app.py                    ponto de entrada — o roteiro da tela
├── requirements.txt
├── .streamlit/config.toml    tema base (dark + vermelho Excenge)
├── ng/
│   ├── config.py             caminhos, colunas, paleta, zooms
│   ├── dados.py              carrega o parquet e aplica filtros
│   ├── classificacao.py      faixas dinâmicas de Ng e cores
│   ├── mapa.py               deck PyDeck
│   ├── ui.py                 sidebar, métricas, legenda, tabela
│   └── estilo/               tema, com fallback rede → local → padrão
├── data/
│   ├── ng_municipios_cache_2026.parquet   2,7 MB — o que o app lê
│   └── ng_municipios.csv                  110 KB — fonte tabular do Ng
└── tools/
    └── gerar_cache.py        regera o parquet (precisa da rede)
```

---

## Sobre os dados

O app lê **um** arquivo: `data/ng_municipios_cache_2026.parquet`. Ele tem 5.488
municípios com geometria já simplificada, CRS EPSG:4326 e o valor de Ng.

A malha municipal do IBGE (`BR_Municipios_2024.shp`, **286 MB**) **não está no
repositório** — o GitHub recusa arquivos acima de 100 MB. Ela serve apenas para
*gerar* o parquet, o que é feito offline:

```bash
python tools/gerar_cache.py
```

Esse script precisa da rede do escritório, onde o shapefile está em
`2 - MATERIAL DE APOIO\1 - NG(SPDA)\`. Rode-o quando a tabela de Ng ou a malha
do IBGE forem atualizadas, e faça commit do parquet resultante.

### Classificação dinâmica

As cinco faixas de cor são recalculadas por quantis **sobre o recorte visível**,
não sobre o Brasil inteiro. Filtrar o Ceará faz "Muito alto" passar a significar
"muito alto para o Ceará".

Isso é intencional: com faixas fixas nacionais, estados de baixa incidência
apareceriam uniformemente azuis e o mapa não mostraria a variação interna — que
é o que interessa a quem dimensiona SPDA numa região específica. Em troca, a cor
**não é comparável entre dois recortes diferentes**; por isso os rótulos dizem
"mínimo local" e "máximo local". Para o valor absoluto, use a tabela ou o
tooltip.

---

## Relação com o app de produção

O app que roda hoje na rede é `1 - PROGRAMA\1 - NG(SPDA)\Ng.py`, com caminhos
apontando para `\\servidor01`. Ele **não foi alterado** e continua funcionando
como sempre.

Esta pasta é uma versão autocontida do mesmo app, reorganizada em módulos e sem
dependência de rede, para publicação no GitHub/Streamlit Cloud. Mudanças de
comportamento feitas aqui precisam ser portadas manualmente para o `Ng.py` de
produção — e vice-versa.
