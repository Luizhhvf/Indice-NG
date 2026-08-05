import streamlit as st
import re
import base64
from pathlib import Path


def _carregar_fundo_svg_datauri():
    """
    Lê o arquivo fundo.html, extrai as cores do :root, substitui as variáveis
    var(--nome) e garante que o SVG tenha viewBox para o CSS conseguir
    esticar as ondas na tela inteira do Streamlit sem cortar ou sumir.
    """
    caminhos_possiveis = [
        Path(__file__).resolve().parent.parent / "fundo.html",
        Path(__file__).resolve().parent / "fundo.html",
        Path("fundo.html").resolve()
    ]
    
    conteudo = None
    for caminho in caminhos_possiveis:
        try:
            if caminho.exists():
                conteudo = caminho.read_text(encoding="utf-8")
                break
        except Exception:
            continue
            
    if not conteudo:
        return None

    try:
        # 1. Mapeia as cores do :root (ex: --cinza-escuro: #303030)
        vars_css = dict(re.findall(r"--([a-zA-Z0-9_-]+)\s*:\s*([^;]+);", conteudo))

        # 2. Captura o bloco <svg>...</svg>
        match = re.search(r"<svg[^>]*>.*?</svg>", conteudo, re.DOTALL | re.IGNORECASE)
        if not match:
            return None
            
        svg_str = match.group(0)

        # 3. Substitui todas as chamadas var(--nome) pelo código hexadecimal real
        for var_nome, var_valor in vars_css.items():
            svg_str = re.sub(rf"var\(\s*--{re.escape(var_nome)}\s*\)", var_valor.strip(), svg_str)

        # 4. Garante que o SVG tenha namespace e viewBox para o background-size: cover funcionar
        if "xmlns=" not in svg_str:
            svg_str = svg_str.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        if "viewBox=" not in svg_str:
            svg_str = svg_str.replace("<svg", '<svg viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice"', 1)

        svg_b64 = base64.b64encode(svg_str.encode("utf-8")).decode("ascii")
        return f'url("data:image/svg+xml;base64,{svg_b64}")'
    except Exception:
        return None


# Logo exibida no rodapé da sidebar. Fica ao lado deste arquivo — sem caminho
# de rede, para o projeto rodar em qualquer máquina e no Streamlit Cloud.
#
# Usamos a variante BRANCA: o azul institucional #004F9F sobre a sidebar
# (#303030 com véu translúcido) dá razão de contraste ~1.6:1, abaixo de
# qualquer limite legível. A arte branca preserva o recorte e o antialiasing
# do original — só o canal de cor muda, o alpha é idêntico.
# Para voltar ao azul, aponte para "logo-uff.png" (o original está mantido).
CAMINHO_LOGO = Path(__file__).resolve().parent / "logo-uff-branca.png"


def _carregar_logo_datauri():
    """Embute a logo como data URI base64 para o CSS.

    Data URI em vez de arquivo servido: o CSS é injetado via ``st.markdown`` e
    não tem como referenciar um caminho do disco do servidor. Embutir resolve
    sem depender de rota estática.

    Devolve ``None`` se a logo não estiver lá — o app roda sem ela.
    """
    try:
        if CAMINHO_LOGO.exists():
            img_b64 = base64.b64encode(CAMINHO_LOGO.read_bytes()).decode("ascii")
            return f'url("data:image/png;base64,{img_b64}")'
    except Exception:
        pass
    return None


def apply_sidebar_style():
    fundo_svg = _carregar_fundo_svg_datauri()
    camada_fundo = fundo_svg if fundo_svg else "none"
    logo_datauri = _carregar_logo_datauri()
    camada_logo = logo_datauri if logo_datauri else "none"

    css = """
    <style>

    /* =====================================================
       EXPANDER NA SIDEBAR
    ===================================================== */
    section[data-testid="stSidebar"] details {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    section[data-testid="stSidebar"] details > div {
        border: none !important;
        background: transparent !important;
        padding: 0 0 0 0.75rem !important;
        margin: 0 !important;
    }
    section[data-testid="stSidebar"] summary {
        border-radius: 6px !important;
        padding: 6px 10px !important;
        font-size: 0.875rem !important;
        font-weight: 400 !important;
        color: inherit !important;
        margin: 0 !important;
    }
    section[data-testid="stSidebar"] summary:hover {
        background-color: rgba(255,255,255,0.08) !important;
    }
    section[data-testid="stSidebar"] summary:focus-visible {
        outline: none !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] details a[data-testid="stPageLink"] {
        border: none !important;
        border-radius: 6px !important;
        background: transparent !important;
        padding: 5px 10px !important;
        font-size: 0.875rem !important;
    }
    section[data-testid="stSidebar"] details a[data-testid="stPageLink"]:hover {
        background-color: rgba(255,255,255,0.08) !important;
    }
    section[data-testid="stSidebar"] details a[data-testid="stPageLink"]:focus,
    section[data-testid="stSidebar"] details a[data-testid="stPageLink"]:active {
        outline: none !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
    }

    /* =====================================================
       PLANO DE FUNDO GERAL — AQUI ESTÁ A CORREÇÃO DA TELA
    ===================================================== */
    :root {
        --dfw-border: rgba(255,255,255,0.09);
        --dfw-radius-lg: 22px;
        --dfw-radius-md: 14px;
    }

    @keyframes dfwRise {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* 1. Aplica o fundo EXCLUSIVAMENTE no contêiner raiz */
    .stApp {
        background-color: #303030 !important;
        background-image: __CAMADA_FUNDO__ !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
        background-size: cover !important;
        background-position: center !important;
    }

    /* 2. FORÇA TRANSPARÊNCIA em todas as camadas internas do Streamlit que cobriam a imagem */
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    [data-testid="stHeader"],
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"],
    [data-testid="stBottomBlockContainer"] > div {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    header[data-testid="stHeader"] {
        backdrop-filter: blur(20px) saturate(120%);
        -webkit-backdrop-filter: blur(20px) saturate(120%);
    }

    section[data-testid="stSidebar"] {
        background-color: transparent !important;
        background-image: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.01)), __CAMADA_LOGO__ !important;
        background-repeat: no-repeat, no-repeat !important;
        background-position: 0 0, bottom 32px center !important;
        background-size: auto, 80% !important;
        backdrop-filter: blur(20px) saturate(120%);
        -webkit-backdrop-filter: blur(20px) saturate(120%);
        border-right: 1px solid rgba(255,255,255,0.09);
    }
    section[data-testid="stSidebar"] > div {
        background: transparent !important;
    }

    section[data-testid="stSidebar"] .stButton > button, 
section[data-testid="stSidebar"] .stFormSubmitButton > button { 
    border-radius: 999px !important; 
    background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.02)) !important; 
    backdrop-filter: blur(16px) saturate(110%); 
    -webkit-backdrop-filter: blur(16px) saturate(110%); 
    border: 1px solid rgba(255,255,255,0.2) !important; 
    transition: transform .15s ease, border-color .2s ease; 
} 

section[data-testid="stSidebar"] .stButton > button:hover, 
section[data-testid="stSidebar"] .stFormSubmitButton > button:hover { 
    transform: translateY(-1px); 
    border-color: rgba(255,255,255,0.4) !important; 
}


    section[data-testid="stSidebar"] [data-testid="stTextInput"] div[data-baseweb="base-input"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.01)) !important;
        backdrop-filter: blur(16px) saturate(110%);
        -webkit-backdrop-filter: blur(16px) saturate(110%);
        border: 1px solid rgba(255,255,255,0.09) !important;
        border-radius: 14px !important;
        transition: border-color .2s ease;
    }
    section[data-testid="stSidebar"] [data-testid="stTextInput"] div[data-baseweb="input"],
    section[data-testid="stSidebar"] [data-testid="stTextInput"] input {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] [data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within {
        border-color: rgba(239,45,60,0.5) !important;
    }

    /* Cards e contêineres de Gráficos */
    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.01)) !important;
        backdrop-filter: blur(20px) saturate(120%);
        -webkit-backdrop-filter: blur(20px) saturate(120%);
        border: 1px solid var(--dfw-border) !important;
        border-radius: var(--dfw-radius-lg) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 8px 24px -16px rgba(0,0,0,0.55);
        transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
        animation: dfwRise .4s ease both;
    }
    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px);
        border-color: rgba(255,255,255,0.22) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.12), 0 18px 36px -18px rgba(0,0,0,0.7);
    }
    
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stVerticalBlockBorderWrapper"] { animation-delay: .02s; }
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stVerticalBlockBorderWrapper"] { animation-delay: .06s; }
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stVerticalBlockBorderWrapper"] { animation-delay: .10s; }
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stVerticalBlockBorderWrapper"] { animation-delay: .14s; }
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > div:nth-child(5) [data-testid="stVerticalBlockBorderWrapper"] { animation-delay: .18s; }

    [data-testid="stMain"] [data-testid="stExpander"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.01)) !important;
        backdrop-filter: blur(20px) saturate(120%);
        -webkit-backdrop-filter: blur(20px) saturate(120%);
        border: 1px solid var(--dfw-border) !important;
        border-radius: var(--dfw-radius-lg) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 8px 24px -16px rgba(0,0,0,0.55);
        animation: dfwRise .4s ease both;
    }
    [data-testid="stMain"] [data-testid="stExpander"] details {
        border: none !important;
        background: transparent !important;
    }
    [data-testid="stMain"] [data-testid="stExpander"] summary {
        border: none !important;
        background: transparent !important;
        border-radius: var(--dfw-radius-lg) var(--dfw-radius-lg) 0 0 !important;
    }
    [data-testid="stMain"] [data-testid="stExpander"] summary:hover,
    [data-testid="stMain"] [data-testid="stExpander"] summary:focus,
    [data-testid="stMain"] [data-testid="stExpander"] summary:focus-visible {
        outline: none !important;
        box-shadow: none !important;
        border: none !important;
    }

    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] a[data-testid="stPageLink"] {
        background: transparent !important;
        border: none !important;
    }

    /* CAIXAS DE ENTRADA PADRÃO */
    [data-testid="stMain"] [data-testid="stTextInput"] div[data-baseweb="base-input"],
    [data-testid="stMain"] [data-testid="stNumberInput"] div[data-baseweb="base-input"],
    [data-testid="stMain"] [data-testid="stDateInput"] div[data-baseweb="base-input"],
    [data-testid="stMain"] [data-testid="stTimeInput"] div[data-baseweb="base-input"],
    [data-testid="stMain"] [data-testid="stTextArea"] div[data-baseweb="base-input"],
    [data-testid="stMain"] [data-testid="stTextArea"] div[data-baseweb="textarea"],
    [data-testid="stMain"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    [data-testid="stMain"] [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
        background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.01)) !important;
        backdrop-filter: blur(16px) saturate(110%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(110%) !important;
        border: 1px solid var(--dfw-border) !important;
        border-radius: var(--dfw-radius-md) !important;
        transition: border-color .2s ease, box-shadow .2s ease;
    }

    [data-testid="stMain"] [data-testid="stTextInput"] div[data-baseweb="input"],
    [data-testid="stMain"] [data-testid="stNumberInput"] div[data-baseweb="input"],
    [data-testid="stMain"] [data-testid="stDateInput"] div[data-baseweb="input"],
    [data-testid="stMain"] [data-testid="stTimeInput"] div[data-baseweb="input"],
    [data-testid="stMain"] [data-testid="stTextInput"] input,
    [data-testid="stMain"] [data-testid="stNumberInput"] input,
    [data-testid="stMain"] [data-testid="stTextArea"] textarea {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* CAIXA DE DIGITAÇÃO E DE HISTÓRICO DO CHAT */
    [data-testid*="stChatInput"],
    [data-testid*="ChatInput"],
    .stChatInput {
        background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.02)) !important;
        background-color: rgba(255,255,255,0.03) !important;
        backdrop-filter: blur(18px) saturate(160%) !important;
        -webkit-backdrop-filter: blur(18px) saturate(160%) !important;
        border: 1px solid var(--dfw-border) !important;
        border-radius: var(--dfw-radius-md) !important;
        box-shadow: 0 6px 30px rgba(0, 0, 0, 0.25) !important;
        transition: border-color .2s ease, box-shadow .2s ease !important;
    }

    [data-testid*="stChatInput"] *,
    [data-testid*="ChatInput"] *,
    .stChatInput * {
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    [data-testid*="stChatInput"] textarea,
    .stChatInput textarea {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    [data-testid*="stChatInput"] textarea::placeholder,
    .stChatInput textarea::placeholder {
        color: rgba(255, 255, 255, 0.45) !important;
        -webkit-text-fill-color: rgba(255, 255, 255, 0.45) !important;
    }

    [data-testid*="stChatInput"]:focus-within,
    .stChatInput:focus-within {
        border-color: rgba(239,45,60,0.6) !important;
        box-shadow: 0 0 14px rgba(239,45,60,0.3) !important;
    }

    [data-testid*="stChatInput"] button,
    .stChatInput button {
        color: rgba(255,255,255,0.6) !important;
        transition: transform .15s ease, color .2s ease !important;
    }
    [data-testid*="stChatInput"] button:hover,
    .stChatInput button:hover {
        transform: scale(1.15) !important;
        color: #ef2d3c !important;
    }

    [data-testid="stChatMessage"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.01)) !important;
        background-color: rgba(255,255,255,0.03) !important;
        backdrop-filter: blur(16px) saturate(110%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(110%) !important;
        border: 1px solid var(--dfw-border) !important;
        border-radius: var(--dfw-radius-md) !important;
        margin-bottom: 1rem !important;
    }
    [data-testid="stChatMessage"] * {
        background-color: transparent !important;
    }

    [data-testid="stMain"] [data-testid="stSelectbox"] svg,
    [data-testid="stMain"] [data-testid="stMultiSelect"] svg {
        opacity: 0.65;
        transition: opacity .2s ease;
    }
    [data-testid="stMain"] [data-testid="stSelectbox"]:hover svg,
    [data-testid="stMain"] [data-testid="stMultiSelect"]:hover svg {
        opacity: 0.95;
    }

    [data-testid="stMain"] [data-testid="stMultiSelect"] div[data-baseweb="select"] > div:focus-within,
    [data-testid="stMain"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
    [data-testid="stMain"] [data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within,
    [data-testid="stMain"] [data-testid="stNumberInput"] div[data-baseweb="base-input"]:focus-within,
    [data-testid="stMain"] [data-testid="stTextArea"] div[data-baseweb="base-input"]:focus-within {
        border-color: rgba(239,45,60,0.5) !important;
        box-shadow: 0 0 0 1px rgba(239,45,60,0.2) !important;
    }

    div[data-baseweb="popover"] * {
        background: transparent !important;
    }
    div[data-baseweb="popover"] ul {
        background: linear-gradient(135deg, rgba(48,48,48,0.92), rgba(35,35,35,0.95)) !important;
        backdrop-filter: blur(20px) saturate(110%);
        -webkit-backdrop-filter: blur(20px) saturate(110%);
        border: 1px solid var(--dfw-border) !important;
        border-radius: var(--dfw-radius-md) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.1), 0 8px 24px -16px rgba(0,0,0,0.6);
        overflow: hidden;
    }
    div[data-baseweb="popover"] li[role="option"]:hover,
    div[data-baseweb="popover"] li[aria-selected="true"],
    div[data-baseweb="popover"] li[role="option"]:hover *,
    div[data-baseweb="popover"] li[aria-selected="true"] * {
        background: rgba(239,45,60,0.22) !important;
    }

    [data-testid="stMain"] [data-testid="stDataFrame"] {
        border: 1px solid var(--dfw-border) !important;
        border-radius: var(--dfw-radius-md) !important;
        overflow: visible;
    }
    /* Recorte arredondado no grid interno para nao cortar a toolbar nativa
       (busca / download / fullscreen fica ancorada no topo do stDataFrame) */
    [data-testid="stMain"] [data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {
        border-radius: var(--dfw-radius-md);
        overflow: hidden;
    }
    /* Garante que a toolbar nativa apareca acima do grid */
    [data-testid="stMain"] [data-testid="stDataFrame"] [data-testid="stElementToolbar"] {
        z-index: 5;
    }

    [data-testid="stMain"] [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.01));
        backdrop-filter: blur(20px) saturate(120%);
        -webkit-backdrop-filter: blur(20px) saturate(120%);
        border: 1px solid var(--dfw-border);
        border-radius: var(--dfw-radius-md);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
        padding: 14px 16px !important;
        animation: dfwRise .4s ease both;
    }
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stMetric"] { animation-delay: .02s; }
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stMetric"] { animation-delay: .08s; }
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stMetric"] { animation-delay: .14s; }
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stMetric"] { animation-delay: .20s; }

    [data-testid="stMain"] .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 1px solid var(--dfw-border);
    }
    [data-testid="stMain"] .stTabs [data-baseweb="tab"] {
        border-radius: 999px 999px 0 0;
        padding: 8px 18px;
    }
    [data-testid="stMain"] .stTabs [aria-selected="true"] {
        color: #ef2d3c !important;
    }
    [data-testid="stMain"] .stTabs [data-baseweb="tab-highlight"] {
        background-color: #ef2d3c !important;
    }

    [data-testid="stMain"] .stButton > button,
    [data-testid="stMain"] .stDownloadButton > button,
    [data-testid="stMain"] .stFormSubmitButton > button,
    [data-testid="stMain"] a[data-testid="stPageLink"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.01)) !important;
        backdrop-filter: blur(20px) saturate(120%);
        -webkit-backdrop-filter: blur(20px) saturate(120%);
        border: 1px solid var(--dfw-border) !important;
        border-radius: 999px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 8px 24px -16px rgba(0,0,0,0.55);
        transition: transform .15s ease, border-color .2s ease, box-shadow .2s ease;
    }
    [data-testid="stMain"] .stButton > button:hover,
    [data-testid="stMain"] .stDownloadButton > button:hover,
    [data-testid="stMain"] .stFormSubmitButton > button:hover,
    [data-testid="stMain"] a[data-testid="stPageLink"]:hover {
        transform: translateY(-2px);
        border-color: rgba(255,255,255,0.22) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.12), 0 18px 36px -18px rgba(0,0,0,0.7);
    }

    /* =====================================================
       CONTRASTE DA SIDEBAR

       O fundo efetivo da sidebar é ~#3C3C3C (a base #303030 do .stApp, mais o
       véu translúcido branco e o blur). Os tons abaixo foram escolhidos contra
       ESSE valor, não contra preto:

         #F0F0F0  títulos e rótulos      ~11.5:1
         #D5D5D5  valores e legenda       ~8.6:1
         #B8B8B8  texto auxiliar          ~6.1:1

       Todos acima de 4.5:1 (WCAG AA para texto normal). O padrão do Streamlit
       para os ticks do slider fica perto de 2:1 sobre este fundo — ilegível,
       que é o problema relatado.
    ===================================================== */

    /* --- Slider: números das pontas e valor do thumb --- */
    section[data-testid="stSidebar"] [data-testid="stSliderTickBarMin"],
    section[data-testid="stSidebar"] [data-testid="stSliderTickBarMax"],
    section[data-testid="stSidebar"] [data-testid="stSliderTickBar"] > div {
        color: #B8B8B8 !important;
        font-weight: 400 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSliderThumbValue"],
    section[data-testid="stSidebar"] [data-testid="stThumbValue"] {
        color: #F0F0F0 !important;
        font-weight: 500 !important;
    }
    /* Trilho: a parte não selecionada precisa ser visível sem competir com a
       faixa ativa, que usa a cor primária do tema. */
    section[data-testid="stSidebar"] [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
        box-shadow: 0 0 0 2px rgba(255,255,255,0.25) !important;
    }

    /* --- Rótulos de widget (selectbox, slider) --- */
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    section[data-testid="stSidebar"] label {
        color: #F0F0F0 !important;
    }

    /* --- Texto corrente, títulos e itens da legenda --- */
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li {
        color: #D5D5D5 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {
        color: #F0F0F0 !important;
    }

    /* --- Valor selecionado no selectbox --- */
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[value],
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        color: #F0F0F0 !important;
    }

    /* --- Ícone de ajuda (o "?" ao lado do título da legenda) --- */
    section[data-testid="stSidebar"] [data-testid="stTooltipIcon"] svg {
        fill: #B8B8B8 !important;
        stroke: #B8B8B8 !important;
    }

    /* --- Divisor: o padrão quase some sobre este fundo --- */
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.16) !important;
    }

    </style>
    """
    css = css.replace("__CAMADA_FUNDO__", camada_fundo)
    css = css.replace("__CAMADA_LOGO__", camada_logo)
    st.markdown(css, unsafe_allow_html=True)