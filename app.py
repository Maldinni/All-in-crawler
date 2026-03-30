import io
import os
import time
import shutil
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from wordcloud import WordCloud

from src.utils.io import ensure_dirs
from src.utils.parsing import parse_args, load_config
from src.utils.pipeline_runner import run_pipeline, PIPELINE_STEPS
from src.utils.data_loader import load_results, search_dataframe

def reset_pipeline_dirs(paths):
    dirs = [
        paths["raw"],
        paths["processed"],
        paths["output"],
        paths["checkpoints"]
    ]

    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d)

    # recria os diretórios vazios
    ensure_dirs(paths["raw"], paths["processed"], paths["checkpoints"], paths["output"])

# ─────────────────────────────────────────────
# Paleta global — usada no Plotly e Matplotlib
# ─────────────────────────────────────────────
PALETTE = {
    "bg":          "#0a0008",
    "surface":     "#1a0d2e",
    "surface2":    "#231240",
    "surface3":    "#2e1a52",
    "border":      "#3d2466",
    "border_l":    "#5a3690",
    "accent":      "#ff6b1a",
    "accent_soft": "#ff8c42",
    "accent2":     "#ffb347",
    "text":        "#f5eeff",
    "text2":       "#b094d4",
    "muted":       "#6e4f96",
}

# Sequência de cores categóricas para séries múltiplas
CAT_COLORS = [
    "#ff6b1a", "#ffb347", "#b094d4", "#7c4dbd",
    "#ff8c42", "#5a3690", "#e05500", "#9c6bcc",
    "#ffd580", "#3d2466",
]

# ─────────────────────────────────────────────
# Tema global Matplotlib — aplicado a todos os figs
# ─────────────────────────────────────────────
def apply_mpl_theme():
    plt.rcParams.update({
        "figure.facecolor":   PALETTE["surface"],
        "axes.facecolor":     PALETTE["surface"],
        "axes.edgecolor":     PALETTE["border"],
        "axes.labelcolor":    PALETTE["text2"],
        "axes.titlecolor":    PALETTE["text"],
        "axes.titlesize":     13,
        "axes.labelsize":     11,
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.grid":          True,
        "grid.color":         PALETTE["border"],
        "grid.linewidth":     0.5,
        "grid.alpha":         0.6,
        "xtick.color":        PALETTE["muted"],
        "ytick.color":        PALETTE["muted"],
        "xtick.labelsize":    9,
        "ytick.labelsize":    9,
        "text.color":         PALETTE["text"],
        "font.family":        "sans-serif",
        "legend.facecolor":   PALETTE["surface2"],
        "legend.edgecolor":   PALETTE["border"],
        "legend.labelcolor":  PALETTE["text2"],
        "legend.fontsize":    9,
    })

# ─────────────────────────────────────────────
# Layout Plotly reutilizável
# ─────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor = PALETTE["surface"],
    plot_bgcolor  = PALETTE["surface"],
    font          = dict(family="DM Sans, sans-serif", color=PALETTE["text"], size=12),
    title_font    = dict(size=14, color=PALETTE["text"]),
    legend        = dict(
        bgcolor     = PALETTE["surface2"],
        bordercolor = PALETTE["border"],
        borderwidth = 1,
        font        = dict(color=PALETTE["text2"], size=11),
    ),
    margin        = dict(l=20, r=20, t=40, b=20),
    xaxis         = dict(
        gridcolor   = PALETTE["border"],
        linecolor   = PALETTE["border"],
        tickcolor   = PALETTE["muted"],
        tickfont    = dict(color=PALETTE["muted"], size=10),
    ),
    yaxis         = dict(
        gridcolor   = PALETTE["border"],
        linecolor   = PALETTE["border"],
        tickcolor   = PALETTE["muted"],
        tickfont    = dict(color=PALETTE["muted"], size=10),
    ),
    hoverlabel    = dict(
        bgcolor     = PALETTE["surface3"],
        bordercolor = PALETTE["accent"],
        font        = dict(color=PALETTE["text"], size=12),
    ),
)

def styled_plotly(fig, height=420):
    """Aplica layout padrão e retorna o fig pronto para st.plotly_chart."""
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    return fig

# ─────────────────────────────────────────────
# Helper: botão de download para fig matplotlib
# ─────────────────────────────────────────────
def download_fig(fig, filename="grafico.png", label="⬇ Baixar PNG"):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight",
                facecolor=PALETTE["surface"])
    st.download_button(label, buf.getvalue(), filename, "image/png",
                       use_container_width=True)

def download_plotly(fig, filename="grafico.png", label="⬇ Baixar PNG"):
    buf = fig.to_image(format="png", scale=2)
    st.download_button(label, buf, filename, "image/png",
                       use_container_width=True)

# ─────────────────────────────────────────────
# Config & Paths
# ─────────────────────────────────────────────
args = parse_args()
cfg  = load_config(args)

paths = cfg["paths"]

result_file = os.path.join(
    cfg["paths"]["processed"],
    "clusters_defined_distinguished_trends_assessed.csv"
)

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Apuração · Agita Comunicação",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS Global
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg:            #0a0008;
    --bg-pure:       #000000;
    --surface:       #1a0d2e;
    --surface-2:     #231240;
    --surface-3:     #2e1a52;
    --border:        #3d2466;
    --border-light:  #5a3690;
    --accent:        #ff6b1a;
    --accent-dim:    rgba(255,107,26,0.15);
    --accent-soft:   #ff8c42;
    --accent-2:      #ffb347;
    --text-primary:  #f5eeff;
    --text-secondary:#b094d4;
    --text-muted:    #6e4f96;
    --radius:        10px;
    --radius-lg:     16px;
    --shadow:        0 1px 4px rgba(0,0,0,.6), 0 4px 20px rgba(10,0,20,.5);
    --font:          'DM Sans', sans-serif;
    --mono:          'DM Mono', monospace;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: var(--bg) !important;
    font-family: var(--font) !important;
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div { padding-top: 1.5rem; }
.block-container { padding: 2rem 2.5rem 4rem !important; max-width: 1280px !important; }

h1,h2,h3,h4 { font-family:var(--font)!important; font-weight:600!important; letter-spacing:-0.02em!important; color:var(--text-primary)!important; }
p,li,span,label,div { font-family:var(--font)!important; color:var(--text-primary); }

/* Sidebar radio */
[data-testid="stSidebar"] .stRadio label { font-size:.875rem!important; color:var(--text-secondary)!important; padding:.45rem .75rem!important; border-radius:6px!important; transition:background .15s,color .15s!important; cursor:pointer; }
[data-testid="stSidebar"] .stRadio label:hover { background:var(--surface-2)!important; color:var(--text-primary)!important; }

/* Buttons */
.stButton>button { background:linear-gradient(135deg,var(--accent),var(--accent-soft))!important; color:#0a0008!important; font-family:var(--font)!important; font-weight:600!important; font-size:.875rem!important; border:none!important; border-radius:var(--radius)!important; padding:.6rem 1.4rem!important; cursor:pointer!important; transition:opacity .15s,transform .1s!important; letter-spacing:.01em!important; }
.stButton>button:hover { opacity:.88!important; transform:translateY(-1px)!important; }
.stButton>button:active { transform:translateY(0)!important; }
.stButton>button:disabled { background:var(--surface-2)!important; color:var(--text-muted)!important; cursor:not-allowed!important; opacity:.5!important; }

/* Inputs */
.stTextInput>div>div>input { background:var(--surface-2)!important; border:1px solid var(--border)!important; border-radius:var(--radius)!important; color:var(--text-primary)!important; font-size:.9rem!important; padding:.55rem .9rem!important; transition:border-color .15s!important; }
.stTextInput>div>div>input:focus { border-color:var(--accent)!important; box-shadow:0 0 0 2px var(--accent-dim)!important; }

/* Sliders */
[data-testid="stSlider"] [data-testid="stThumbValue"] { background:var(--accent)!important; color:#0a0008!important; }
[data-testid="stSlider"] > div > div > div { background:var(--border)!important; }
[data-testid="stSlider"] > div > div > div > div { background:linear-gradient(90deg,var(--accent),var(--accent-soft))!important; }

/* Selectbox / Multiselect */
[data-testid="stSelectbox"] > div, [data-testid="stMultiSelect"] > div { background:var(--surface-2)!important; border:1px solid var(--border)!important; border-radius:var(--radius)!important; }
[data-testid="stMultiSelect"] span[data-baseweb="tag"] { background:var(--surface-3)!important; border:1px solid var(--border-light)!important; }

/* Date input */
[data-testid="stDateInput"] input { background:var(--surface-2)!important; border:1px solid var(--border)!important; border-radius:var(--radius)!important; color:var(--text-primary)!important; }

/* DataFrame */
[data-testid="stDataFrame"] { border:1px solid var(--border)!important; border-radius:var(--radius-lg)!important; overflow:hidden!important; }

/* Progress */
[data-testid="stProgressBar"]>div>div { background:linear-gradient(90deg,var(--accent),var(--accent-2))!important; border-radius:9999px!important; }
[data-testid="stProgressBar"]>div { background:var(--surface-2)!important; border-radius:9999px!important; }

/* Metrics */
[data-testid="stMetric"] { background:var(--surface)!important; border:1px solid var(--border)!important; border-radius:var(--radius-lg)!important; padding:1.1rem 1.4rem!important; box-shadow:var(--shadow)!important; transition:border-color .2s,box-shadow .2s!important; }
[data-testid="stMetric"]:hover { border-color:var(--accent)!important; box-shadow:var(--shadow),0 0 18px var(--accent-dim)!important; }
[data-testid="stMetricLabel"] { color:var(--text-secondary)!important; font-size:.8rem!important; font-weight:500!important; text-transform:uppercase; letter-spacing:.06em; }
[data-testid="stMetricValue"] { color:var(--accent-soft)!important; font-size:1.7rem!important; font-weight:600!important; }

/* Tabs */
[data-testid="stTabs"] [role="tablist"] { background:var(--surface)!important; border:1px solid var(--border)!important; border-radius:var(--radius)!important; padding:3px!important; gap:2px!important; }
[data-testid="stTabs"] [role="tab"] { border-radius:7px!important; font-size:.85rem!important; font-weight:500!important; color:var(--text-secondary)!important; padding:.4rem 1rem!important; border:none!important; transition:background .15s,color .15s!important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { background:var(--surface-3)!important; color:var(--accent-soft)!important; box-shadow:inset 0 0 0 1px var(--border-light)!important; }

/* Expander */
[data-testid="stExpander"] { background:var(--surface)!important; border:1px solid var(--border)!important; border-radius:var(--radius-lg)!important; overflow:hidden!important; }
[data-testid="stExpander"] summary { font-weight:500!important; color:var(--text-secondary)!important; }

/* Alerts */
[data-testid="stAlert"] { border-radius:var(--radius)!important; border:1px solid var(--border)!important; background:var(--surface-2)!important; font-size:.875rem!important; }

/* Plotly container */
[data-testid="stPlotlyChart"] { border-radius:var(--radius-lg)!important; overflow:hidden!important; }

/* Pyplot */
[data-testid="stImage"],.stPyplot { border-radius:var(--radius-lg)!important; overflow:hidden!important; }

/* Scrollbar */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:var(--surface); }
::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:99px; }
hr { border-color:var(--border)!important; }

/* Sidebar logo */
[data-testid="stSidebar"] [data-testid="stImage"] { display:block!important; margin:0 auto!important; filter:brightness(0) invert(1) sepia(1) saturate(3) hue-rotate(310deg) brightness(1.1)!important; }
[data-testid="stSidebar"] [data-testid="stImage"] img { border-radius:0!important; }

/* Shared utility classes */
.nt-section-label { font-size:.7rem; text-transform:uppercase; letter-spacing:.1em; color:var(--text-muted); font-weight:600; margin:0 0 .6rem; }
.nt-page-header { margin-bottom:2rem; padding-bottom:1.25rem; border-bottom:1px solid var(--border); position:relative; }
.nt-page-header::after { content:''; position:absolute; bottom:-1px; left:0; width:64px; height:2px; background:linear-gradient(90deg,var(--accent),var(--accent-2)); border-radius:9999px; }
.nt-page-header h1 { font-size:1.6rem!important; margin:0!important; }
.nt-page-header p  { color:var(--text-secondary); font-size:.9rem; margin:.3rem 0 0; }
.nt-step-running { color:var(--accent-soft); font-size:.85rem; font-weight:500; }
.nt-step-done    { color:var(--accent);       font-size:.85rem; font-weight:500; }
.nt-step-pending { color:var(--text-muted);   font-size:.85rem; }
.nt-log { height:360px; overflow-y:auto; background:var(--bg-pure); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1rem 1.2rem; font-family:var(--mono); font-size:.78rem; line-height:1.7; color:var(--accent-soft); }
.nt-chart-wrap { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1.25rem 1.5rem 1rem; margin-bottom:1.25rem; box-shadow:var(--shadow); transition:border-color .2s; }
.nt-chart-wrap:hover { border-color:var(--border-light); }
.nt-chart-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:.75rem; }
.nt-chart-title { font-size:.8rem; font-weight:600; color:var(--accent-soft); text-transform:uppercase; letter-spacing:.08em; padding-left:.6rem; border-left:2px solid var(--accent); }
.nt-controls-bar { background:var(--surface-2); border:1px solid var(--border); border-radius:var(--radius); padding:.75rem 1rem; margin-bottom:1rem; display:flex; gap:1rem; align-items:center; flex-wrap:wrap; }

/* Sobre page */
.ap-hero { background:linear-gradient(135deg,var(--surface-2) 0%,var(--surface-3) 100%); border:1px solid var(--border-light); border-radius:var(--radius-lg); padding:2.5rem 2rem; margin-bottom:2rem; position:relative; overflow:hidden; }
.ap-hero::before { content:''; position:absolute; top:-60px; right:-60px; width:220px; height:220px; background:radial-gradient(circle,rgba(255,107,26,.12) 0%,transparent 70%); pointer-events:none; }
.ap-hero-tag { display:inline-block; font-size:.7rem; font-weight:700; text-transform:uppercase; letter-spacing:.12em; color:var(--accent); border:1px solid var(--accent-dim); background:rgba(255,107,26,.08); border-radius:99px; padding:.2rem .75rem; margin-bottom:1rem; }
.ap-hero h2 { font-size:2rem!important; font-weight:700!important; color:var(--text-primary)!important; margin:0 0 .6rem!important; line-height:1.2!important; }
.ap-hero p  { color:var(--text-secondary)!important; font-size:1rem; max-width:640px; line-height:1.7; margin:0!important; }
.ap-feature-card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1.4rem; height:100%; transition:border-color .2s,box-shadow .2s; }
.ap-feature-card:hover { border-color:var(--accent); box-shadow:0 0 20px var(--accent-dim); }
.ap-feature-icon  { font-size:1.5rem; margin-bottom:.75rem; display:block; }
.ap-feature-title { font-size:.95rem!important; font-weight:600!important; color:var(--text-primary)!important; margin:0 0 .4rem!important; }
.ap-feature-desc  { font-size:.82rem!important; color:var(--text-secondary)!important; line-height:1.6!important; margin:0!important; }
.ap-step-card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1.4rem 1.4rem 1.4rem 1.1rem; border-left:3px solid var(--accent); height:100%; }
.ap-step-number { font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.1em; color:var(--accent); margin-bottom:.4rem; }
.ap-step-title  { font-size:.9rem!important; font-weight:600!important; color:var(--text-primary)!important; margin:0 0 .3rem!important; }
.ap-step-desc   { font-size:.8rem!important; color:var(--text-secondary)!important; line-height:1.55!important; margin:0!important; }
.ap-usecase-card  { background:var(--surface-2); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1.25rem; }
.ap-usecase-title { font-size:.85rem!important; font-weight:700!important; color:var(--accent-soft)!important; text-transform:uppercase; letter-spacing:.06em; margin:0 0 .75rem!important; }
.ap-usecase-item  { font-size:.82rem!important; color:var(--text-secondary)!important; padding:.2rem 0; display:flex; gap:.4rem; align-items:flex-start; line-height:1.5; }
.ap-section-title { font-size:1.1rem!important; font-weight:700!important; color:var(--text-primary)!important; margin:0 0 .25rem!important; letter-spacing:-.01em!important; }
.ap-section-sub   { font-size:.85rem!important; color:var(--text-secondary)!important; margin:0 0 1.5rem!important; }
.ap-divider       { border:none; border-top:1px solid var(--border); margin:2rem 0; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("D:/github/All-in-crawler/logoofcapudados.png", width=160)
    st.markdown('<hr style="border-color:var(--border);margin:.75rem 0 1rem">', unsafe_allow_html=True)
    st.markdown('<p class="nt-section-label">Navegação</p>', unsafe_allow_html=True)
    page = st.radio(
        label="nav",
        options=["Sobre", "Executar Pipeline", "Resultados", "Visualizações"],
        label_visibility="collapsed"
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:0 .5rem">
        <p style="font-size:.72rem;color:#6e4f96;line-height:1.6">
            Plataforma de inteligência de narrativas da
            <span style="color:#b094d4;font-weight:600">Agita Comunicação</span>.
            Análise semântica e identificação de tendências em tempo real.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# PÁGINA: SOBRE
# ══════════════════════════════════════════════
if page == "Sobre":

    st.markdown("""
    <div class="ap-hero">
        <span class="ap-hero-tag">Agita Comunicação · Plataforma</span>
        <h2>Inteligência de Narrativas<br>para o Debate Público</h2>
        <p>O Apuração transforma grandes volumes de dados digitais em insights estratégicos e acionáveis —
           identificando tendências emergentes antes mesmo de chegarem à grande mídia.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="ap-section-title">Dimensões de Análise</p>', unsafe_allow_html=True)
    st.markdown('<p class="ap-section-sub">O que a plataforma monitora e classifica em tempo real</p>', unsafe_allow_html=True)
    dims = [
        ("📈","Tendências","Temas que estão ganhando ou perdendo relevância no debate público."),
        ("🗣️","Narrativas","Como os assuntos são construídos e disseminados pelo público."),
        ("💬","Tom Emocional","Sentimento predominante e reações nas discussões digitais."),
        ("⚖️","Viés Político","Posicionamentos ideológicos e grau de polarização."),
        ("👤","Atores","Perfis e organizações que lideram e impulsionam o debate."),
    ]
    for col, (icon, title, desc) in zip(st.columns(5, gap="small"), dims):
        with col:
            st.markdown(f'<div class="ap-feature-card"><span class="ap-feature-icon">{icon}</span><p class="ap-feature-title">{title}</p><p class="ap-feature-desc">{desc}</p></div>', unsafe_allow_html=True)

    st.markdown('<hr class="ap-divider">', unsafe_allow_html=True)
    st.markdown('<p class="ap-section-title">Como Funciona</p>', unsafe_allow_html=True)
    st.markdown('<p class="ap-section-sub">Pipeline de 4 etapas — da coleta ao insight</p>', unsafe_allow_html=True)
    pipeline_steps = [
        ("01","Coleta de Dados","Monitoramento abrangente de notícias, redes sociais e conteúdos digitais públicos em tempo real."),
        ("02","Ciência de Dados","Tratamento, organização e identificação de padrões complexos em grandes volumes de informação."),
        ("03","IA Proprietária","Análise semântica e classificação de narrativas com modelos exclusivos desenvolvidos pela Agita."),
        ("04","Extração de Insights","Tradução de dados complexos em informações claras e acionáveis para suporte à decisão."),
    ]
    for col, (num, title, desc) in zip(st.columns(4, gap="medium"), pipeline_steps):
        with col:
            st.markdown(f'<div class="ap-step-card"><p class="ap-step-number">Etapa {num}</p><p class="ap-step-title">{title}</p><p class="ap-step-desc">{desc}</p></div>', unsafe_allow_html=True)

    st.markdown('<hr class="ap-divider">', unsafe_allow_html=True)
    st.markdown('<p class="ap-section-title">Casos de Uso</p>', unsafe_allow_html=True)
    st.markdown('<p class="ap-section-sub">Quem usa e para quê</p>', unsafe_allow_html=True)
    usecases = [
        ("📰 Jornalismo",["Identificação de pautas emergentes","Análise de tendências sociais","Monitoramento de debates relevantes"]),
        ("🗳️ Política",["Acompanhamento de narrativas eleitorais","Análise de polarização","Monitoramento de opinião pública"]),
        ("🏢 Empresas",["Monitoramento de reputação","Identificação precoce de crises","Análise de percepção pública"]),
        ("📣 Influenciadores",["Descoberta de tendências","Identificação de temas em ascensão","Engajamento com narrativas virais"]),
    ]
    for col, (title, items) in zip(st.columns(4, gap="medium"), usecases):
        with col:
            items_html = "".join(f'<div class="ap-usecase-item"><span style="color:var(--accent)">›</span>{i}</div>' for i in items)
            st.markdown(f'<div class="ap-usecase-card"><p class="ap-usecase-title">{title}</p>{items_html}</div>', unsafe_allow_html=True)

    st.markdown('<hr class="ap-divider">', unsafe_allow_html=True)
    col_diff, col_ins = st.columns(2, gap="large")
    with col_diff:
        st.markdown('<p class="ap-section-title">Diferencial Tecnológico</p>', unsafe_allow_html=True)
        st.markdown('<p class="ap-section-sub">Por que o Apuração é único</p>', unsafe_allow_html=True)
        for icon, title, desc in [
            ("🧠","IA Proprietária","Modelos desenvolvidos especificamente para análise de narrativas e opinião pública."),
            ("⚡","Escalabilidade","Processa grandes volumes de dados sociais complexos em tempo real."),
            ("🔍","Controle Metodológico","Metodologias auditáveis, garantindo resultados confiáveis e transparentes."),
            ("🔒","Independência","Livre de dependência de modelos comerciais externos."),
        ]:
            st.markdown(f'<div class="ap-feature-card" style="margin-bottom:.75rem;display:flex;gap:.9rem;align-items:flex-start;padding:1rem 1.2rem"><span style="font-size:1.2rem;flex-shrink:0">{icon}</span><div><p class="ap-feature-title" style="margin-bottom:.2rem!important">{title}</p><p class="ap-feature-desc">{desc}</p></div></div>', unsafe_allow_html=True)
    with col_ins:
        st.markdown('<p class="ap-section-title">Insights Estratégicos</p>', unsafe_allow_html=True)
        st.markdown('<p class="ap-section-sub">O que você ganha com a plataforma</p>', unsafe_allow_html=True)
        for icon, title, desc in [
            ("⏩","Antecipação","Posicione-se à frente do debate antes que as tendências cheguem à grande mídia."),
            ("🎯","Público","Compreensão profunda das mudanças de humor e interesse do seu público-alvo."),
            ("📡","Influenciadores","Identificação precisa dos atores que realmente impactam sua narrativa."),
            ("⏱️","Tempo Real","Acompanhamento contínuo para ajustes rápidos em estratégias de comunicação."),
            ("📊","Decisões","Tomada de decisões baseada em dados concretos, reduzindo riscos e incertezas."),
        ]:
            st.markdown(f'<div class="ap-feature-card" style="margin-bottom:.75rem;display:flex;gap:.9rem;align-items:flex-start;padding:1rem 1.2rem"><span style="font-size:1.2rem;flex-shrink:0">{icon}</span><div><p class="ap-feature-title" style="margin-bottom:.2rem!important">{title}</p><p class="ap-feature-desc">{desc}</p></div></div>', unsafe_allow_html=True)

    st.markdown('<hr class="ap-divider">', unsafe_allow_html=True)
    st.markdown('<p class="ap-section-title">Relatórios e Análises</p>', unsafe_allow_html=True)
    st.markdown('<p class="ap-section-sub">Formatos de entrega disponíveis</p>', unsafe_allow_html=True)
    for col, (icon, title, desc) in zip(st.columns(4, gap="medium"), [
        ("📋","Tendências","Visão macro sobre o que está por vir no cenário digital e debates emergentes."),
        ("🗺️","Narrativas","Estudo detalhado sobre a construção, disseminação e impacto de discursos públicos."),
        ("📡","Monitoramento","Acompanhamento contínuo de temas sensíveis e críticos para a reputação do cliente."),
        ("📄","Personalizados","Documentos formatados sob demanda para suporte à tomada de decisão executiva."),
    ]):
        with col:
            st.markdown(f'<div class="ap-step-card"><p class="ap-step-number">{icon}</p><p class="ap-step-title">{title}</p><p class="ap-step-desc">{desc}</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:var(--surface-2);border:1px solid var(--border-light);border-radius:var(--radius-lg);padding:1.75rem 2rem;text-align:center">
        <p style="font-size:1rem;font-weight:700;color:var(--text-primary);margin:0 0 .4rem">Agita Comunicação</p>
        <p style="font-size:.85rem;color:var(--text-secondary);margin:0 0 .25rem">Agência dedicada à análise de informação, comunicação estratégica e inteligência de dados de alto impacto.</p>
        <p style="font-size:.82rem;color:var(--text-muted);margin:0">Para saber mais ou solicitar uma demonstração, entre em contato com a Agita Comunicação.</p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# PÁGINA: EXECUTAR PIPELINE
# ══════════════════════════════════════════════
elif page == "Executar Pipeline":

    st.markdown("""
    <div class="nt-page-header">
        <h1>Executar Pipeline</h1>
        <p>Inicie o pipeline completo de análise para gerar clusters e tendências atualizadas.</p>
    </div>
    """, unsafe_allow_html=True)

    step_status = {name: "pending" for name, _ in PIPELINE_STEPS}

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        run_button = st.button("▶  Iniciar Pipeline",
                               disabled=st.session_state.get("running", False),
                               use_container_width=True)

    progress_bar = st.progress(0)
    status_text  = st.empty()
    st.markdown("<br>", unsafe_allow_html=True)

    col_steps, col_logs = st.columns([1, 2], gap="large")
    with col_steps:
        st.markdown('<p class="nt-section-label">Etapas</p>', unsafe_allow_html=True)
        status_container = st.container()
    with col_logs:
        st.markdown('<p class="nt-section-label">Log de Execução</p>', unsafe_allow_html=True)
        log_placeholder = st.empty()

    def render_steps():
        status_container.empty()
        with status_container:
            for step, status in step_status.items():
                if status == "done":
                    st.markdown(f'<p class="nt-step-done">✓ &nbsp;{step}</p>', unsafe_allow_html=True)
                elif status == "running":
                    st.markdown(f'<p class="nt-step-running">◌ &nbsp;{step}</p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p class="nt-step-pending">○ &nbsp;{step}</p>', unsafe_allow_html=True)

    render_steps()

    if run_button:
        st.session_state["running"] = True
        logs = []

        # limpa dados antigos
        #reset_pipeline_dirs(paths)

        def log_callback(message):
            logs.append(message)
            log_placeholder.markdown(
                f'<div class="nt-log"><pre>{"".join(logs)}</pre></div>',
                unsafe_allow_html=True
            )

        try:
            status_text.info("Pipeline em execução…")
            run_pipeline(log_callback)
            progress_bar.progress(1.0)
            status_text.success("Pipeline concluído com sucesso.")
        except Exception as e:
            st.error(f"Falha no pipeline: {str(e)}")
        finally:
            st.session_state["running"] = False


# ══════════════════════════════════════════════
# PÁGINA: RESULTADOS
# ══════════════════════════════════════════════
elif page == "Resultados":

    st.markdown("""
    <div class="nt-page-header">
        <h1>Resultados dos Clusters</h1>
        <p>Navegue, pesquise e inspecione os dados de clusters gerados pelo pipeline.</p>
    </div>
    """, unsafe_allow_html=True)

    if not os.path.exists(result_file):
        st.warning("Nenhum resultado encontrado. Execute o pipeline primeiro.")
        st.stop()

    df = load_results(result_file)

    total_rows      = len(df)
    total_cols      = len(df.columns)
    unique_clusters = df["cluster"].nunique() if "cluster" in df.columns else "—"
    col_name = "source" if "source" in df.columns else (df.columns[0] if len(df.columns) else "—")
    total_sources   = df[col_name].nunique() if col_name in df.columns else "—"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Registros", f"{total_rows:,}")
    m2.metric("Clusters Únicos",    str(unique_clusters))
    m3.metric("Fontes",             str(total_sources))
    m4.metric("Colunas",            total_cols)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Filtros da tabela ──
    with st.expander("🔧  Filtros e Colunas", expanded=True):
        fc1, fc2, fc3 = st.columns([2, 1, 1])
        with fc1:
            keyword = st.text_input(
                label="busca", placeholder="🔍  Buscar em todas as colunas…",
                label_visibility="collapsed"
            )
        with fc2:
            if "cluster" in df.columns:
                cluster_opts = ["Todos"] + sorted(df["cluster"].unique().tolist())
                cluster_filter = st.selectbox("Cluster", cluster_opts)
            else:
                cluster_filter = "Todos"
        with fc3:
            rows_per_page = st.selectbox("Linhas por página", [25, 50, 100, 200], index=1)

        visible_cols = st.multiselect(
            "Colunas visíveis", options=df.columns.tolist(),
            default=df.columns.tolist(),
            help="Selecione quais colunas exibir"
        )

    # Aplicar filtros
    filtered_df = search_dataframe(df, keyword)
    if cluster_filter != "Todos" and "cluster" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["cluster"] == cluster_filter]
    if visible_cols:
        filtered_df = filtered_df[visible_cols]

    # Paginação simples
    total_filtered = len(filtered_df)
    max_page = max(1, (total_filtered - 1) // rows_per_page + 1)
    page_num = st.number_input("Página", min_value=1, max_value=max_page, value=1, step=1)
    start_idx = (page_num - 1) * rows_per_page
    page_df   = filtered_df.iloc[start_idx : start_idx + rows_per_page]

    st.markdown(
        f'<p style="font-size:.8rem;color:var(--text-muted);margin-bottom:.5rem">'
        f'{total_filtered:,} resultado{"s" if total_filtered != 1 else ""}  ·  '
        f'página {page_num} de {max_page}</p>',
        unsafe_allow_html=True
    )
    st.dataframe(page_df, use_container_width=True, height=460)

    # Download da tabela filtrada
    csv_buf = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Baixar CSV filtrado", csv_buf,
        "resultados_filtrados.csv", "text/csv",
        use_container_width=False
    )



# ══════════════════════════════════════════════
# PÁGINA: VISUALIZAÇÕES
# Usa as funções originais do matplotlib_charts.py
# + tema visual aplicado via apply_mpl_theme()
# + controles Streamlit (Top N, filtro Focus, período)
# + botão de download PNG em cada gráfico
# ══════════════════════════════════════════════
elif page == "Visualizações":

    # Importa as funções originais — lógica 100% preservada
    from src.visualizations.matplotlib_charts import (
        focus_pie_chart,
        focus_bar_chart,
        keywords_wordcloud,
        focus_weighted_importance_chart,
        temporal_trend_chart,
        top_sources_chart,
        source_focus_distribution_chart,
        keyword_weight_chart,
    )

    st.markdown("""
    <div class="nt-page-header">
        <h1>Visualizações</h1>
        <p>Explore distribuição de clusters, tendências temporais e análise de palavras-chave.</p>
    </div>
    """, unsafe_allow_html=True)

    if not os.path.exists(result_file):
        st.warning("Nenhum resultado encontrado. Execute o pipeline primeiro.")
        st.stop()

    clusters_df = pd.read_csv(result_file)

    # ── Aplicar tema matplotlib globalmente ──
    apply_mpl_theme()

    # ── Painel de controles global ──
    with st.expander("⚙️  Controles Globais", expanded=True):
        ctrl1, ctrl2 = st.columns([1, 1])
        with ctrl1:
            top_n = st.slider(
                "Top N temas / fontes / keywords",
                min_value=3, max_value=30, value=10,
                help="Controla quantos itens são exibidos nos rankings e nos gráficos"
            )
        with ctrl2:
            chart_height = st.slider(
                "Altura dos gráficos (px)",
                min_value=300, max_value=800, value=520, step=20,
                help="Ajusta a altura de todos os gráficos da página"
            )

        # Filtro de Focus (coluna real do CSV)
        if "Focus" in clusters_df.columns:
            all_focus = sorted(
                clusters_df["Focus"].dropna()
                .str.split("|").explode().str.strip().unique().tolist()
            )
            selected_focus = st.multiselect(
                "Filtrar por tema (Focus)",
                options=all_focus,
                default=[],
                placeholder="Todos os temas — selecione para filtrar",
                help="Filtra as linhas do CSV cujo campo Focus contém os temas selecionados"
            )
        else:
            selected_focus = []

    # Aplicar filtro de Focus no DataFrame
    if selected_focus:
        mask = clusters_df["Focus"].dropna().str.split("|").apply(
            lambda lst: any(f.strip() in selected_focus for f in lst)
        )
        viz_df = clusters_df.loc[mask.index[mask]].copy()
    else:
        viz_df = clusters_df.copy()

    # Salvar versão filtrada em temp para passar às funções que leem CSV por path
    import tempfile, os as _os
    _tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    viz_df.to_csv(_tmp.name, index=False)
    filtered_result_file = _tmp.name

    # ────────────────────────────────────────────
    # TABS
    # ────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "  📊  Distribuição  ",
        "  📈  Tendências  ",
        "  🗞️  Fontes  ",
        "  🔤  Palavras-chave  ",
    ])

    # ══════════════════════════════════════
    # TAB 1 — DISTRIBUIÇÃO
    # Funções originais: focus_pie_chart, focus_bar_chart,
    #                    focus_weighted_importance_chart
    # ══════════════════════════════════════
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        c_left, c_right = st.columns(2, gap="large")

        with c_left:
            st.markdown(
                '<div class="nt-chart-wrap">'
                '<div class="nt-chart-header"><span class="nt-chart-title">Distribuição de Temas</span></div>',
                unsafe_allow_html=True
            )
            with st.spinner("Gerando gráfico…"):
                fig1 = focus_pie_chart(filtered_result_file)
                # Aplicar tema ao fig retornado
                fig1.patch.set_facecolor(PALETTE["surface"])
                for ax in fig1.get_axes():
                    ax.set_facecolor(PALETTE["surface"])
                fig1.set_size_inches(7, chart_height / 96)
                st.pyplot(fig1, use_container_width=True)
                download_fig(fig1, "distribuicao_temas.png")
                plt.close(fig1)
            st.markdown('</div>', unsafe_allow_html=True)

        with c_right:
            st.markdown(
                '<div class="nt-chart-wrap">'
                '<div class="nt-chart-header"><span class="nt-chart-title">Frequência de Temas</span></div>',
                unsafe_allow_html=True
            )
            with st.spinner("Gerando gráfico…"):
                fig2 = focus_bar_chart(filtered_result_file)
                fig2.patch.set_facecolor(PALETTE["surface"])
                for ax in fig2.get_axes():
                    ax.set_facecolor(PALETTE["surface"])
                fig2.set_size_inches(9, chart_height / 96)
                st.pyplot(fig2, use_container_width=True)
                download_fig(fig2, "frequencia_temas.png")
                plt.close(fig2)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="nt-chart-wrap">'
            '<div class="nt-chart-header"><span class="nt-chart-title">Importância Ponderada por Cluster</span></div>',
            unsafe_allow_html=True
        )
        with st.spinner("Gerando gráfico…"):
            fig3 = focus_weighted_importance_chart(filtered_result_file)
            fig3.patch.set_facecolor(PALETTE["surface"])
            for ax in fig3.get_axes():
                ax.set_facecolor(PALETTE["surface"])
            fig3.set_size_inches(10, chart_height / 96)
            st.pyplot(fig3, use_container_width=True)
            download_fig(fig3, "importancia_ponderada.png")
            plt.close(fig3)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════
    # TAB 2 — TENDÊNCIAS TEMPORAIS
    # Função original: temporal_trend_chart
    # + controles de período e granularidade
    # ══════════════════════════════════════
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)

        # Controles de período — lidos antes de chamar a função
        articles_path = cfg["paths"]["processed"]
        articles_file_check = _os.path.join(articles_path, "articles_merged_cleaned_clustered_organized.csv")

        if _os.path.exists(articles_file_check):
            _art_df = pd.read_csv(articles_file_check, usecols=["publish_date"])
            _art_df["publish_date"] = pd.to_datetime(_art_df["publish_date"], errors="coerce", utc=True)
            _art_df = _art_df.dropna(subset=["publish_date"])
            _art_df["publish_date"] = _art_df["publish_date"].dt.tz_localize(None)

            if not _art_df.empty:
                tc1, tc2 = st.columns([1, 2])
                with tc1:
                    granularity = st.selectbox(
                        "Granularidade", ["Diária", "Semanal", "Mensal"], index=1,
                        help="Agrupa as publicações por dia, semana ou mês"
                    )
                with tc2:
                    _dmin = _art_df["publish_date"].min().date()
                    _dmax = _art_df["publish_date"].max().date()
                    date_range = st.date_input(
                        "Período de análise",
                        value=(_dmin, _dmax),
                        min_value=_dmin, max_value=_dmax,
                        help="Filtra os artigos dentro deste intervalo de datas"
                    )

        st.markdown(
            '<div class="nt-chart-wrap">'
            '<div class="nt-chart-header"><span class="nt-chart-title">Tendência Temporal dos Principais Temas</span></div>',
            unsafe_allow_html=True
        )
        with st.spinner("Gerando gráfico…"):
            try:
                fig4 = temporal_trend_chart(cfg["paths"]["processed"], filtered_result_file)
                fig4.patch.set_facecolor(PALETTE["surface"])
                for ax in fig4.get_axes():
                    ax.set_facecolor(PALETTE["surface"])
                fig4.set_size_inches(11, chart_height / 96)
                st.pyplot(fig4, use_container_width=True)
                download_fig(fig4, "tendencia_temporal.png")
                plt.close(fig4)
            except Exception as e:
                st.error(f"Erro ao gerar tendência temporal: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════
    # TAB 3 — FONTES
    # Funções originais: top_sources_chart,
    #                    source_focus_distribution_chart
    # ══════════════════════════════════════
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        c_left2, c_right2 = st.columns(2, gap="large")

        with c_left2:
            st.markdown(
                '<div class="nt-chart-wrap">'
                '<div class="nt-chart-header"><span class="nt-chart-title">Top Fontes</span></div>',
                unsafe_allow_html=True
            )
            with st.spinner("Gerando gráfico…"):
                try:
                    fig5 = top_sources_chart(cfg["paths"]["processed"])
                    fig5.patch.set_facecolor(PALETTE["surface"])
                    for ax in fig5.get_axes():
                        ax.set_facecolor(PALETTE["surface"])
                    fig5.set_size_inches(10, chart_height / 96)
                    st.pyplot(fig5, use_container_width=True)
                    download_fig(fig5, "top_fontes.png")
                    plt.close(fig5)
                except Exception as e:
                    st.error(f"Erro ao gerar top fontes: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        with c_right2:
            st.markdown(
                '<div class="nt-chart-wrap">'
                '<div class="nt-chart-header"><span class="nt-chart-title">Distribuição de Temas por Fonte</span></div>',
                unsafe_allow_html=True
            )
            with st.spinner("Gerando gráfico…"):
                try:
                    fig6 = source_focus_distribution_chart(cfg["paths"]["processed"], filtered_result_file)
                    fig6.patch.set_facecolor(PALETTE["surface"])
                    for ax in fig6.get_axes():
                        ax.set_facecolor(PALETTE["surface"])
                    fig6.set_size_inches(12, chart_height / 96)
                    st.pyplot(fig6, use_container_width=True)
                    download_fig(fig6, "temas_por_fonte.png")
                    plt.close(fig6)
                except Exception as e:
                    st.error(f"Erro ao gerar distribuição por fonte: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════
    # TAB 4 — PALAVRAS-CHAVE
    # Funções originais: keyword_weight_chart,
    #                    keywords_wordcloud
    # + wordcloud com colormap da paleta
    # ══════════════════════════════════════
    with tab4:
        st.markdown("<br>", unsafe_allow_html=True)
        c_left3, c_right3 = st.columns(2, gap="large")

        with c_left3:
            st.markdown(
                '<div class="nt-chart-wrap">'
                '<div class="nt-chart-header"><span class="nt-chart-title">Palavras-chave por Peso</span></div>',
                unsafe_allow_html=True
            )
            with st.spinner("Gerando gráfico…"):
                try:
                    fig7 = keyword_weight_chart(viz_df)
                    fig7.patch.set_facecolor(PALETTE["surface"])
                    for ax in fig7.get_axes():
                        ax.set_facecolor(PALETTE["surface"])
                        # Recolorir barras com gradiente laranja
                        bars = ax.patches
                        n = len(bars)
                        for i, bar in enumerate(bars):
                            t = i / max(n - 1, 1)
                            r = int(0x2e + t * (0xff - 0x2e))
                            g = int(0x1a + t * (0x6b - 0x1a))
                            b = int(0x52 + t * (0x1a - 0x52))
                            bar.set_facecolor(f"#{r:02x}{g:02x}{b:02x}")
                        ax.tick_params(colors=PALETTE["text2"])
                        ax.xaxis.label.set_color(PALETTE["text2"])
                        ax.yaxis.label.set_color(PALETTE["text2"])
                        ax.title.set_color(PALETTE["text"])
                        for spine in ax.spines.values():
                            spine.set_edgecolor(PALETTE["border"])
                    fig7.set_size_inches(10, chart_height / 96)
                    st.pyplot(fig7, use_container_width=True)
                    download_fig(fig7, "keywords_peso.png")
                    plt.close(fig7)
                except Exception as e:
                    st.error(f"Erro ao gerar keywords: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        with c_right3:
            st.markdown(
                '<div class="nt-chart-wrap">'
                '<div class="nt-chart-header"><span class="nt-chart-title">Nuvem de Palavras-chave</span></div>',
                unsafe_allow_html=True
            )
            with st.spinner("Gerando gráfico…"):
                try:
                    # Substitui a wordcloud original por uma com tema aplicado
                    # (mesma lógica interna, colormap customizado)
                    import matplotlib.colors as mcolors
                    if "Keywords" in viz_df.columns and "Size" in viz_df.columns:
                        kw_exp = (
                            viz_df[["Keywords", "Size"]]
                            .dropna()
                            .assign(Keywords=lambda x: x["Keywords"].str.split(";"))
                            .explode("Keywords")
                        )
                        kw_exp["Keywords"] = kw_exp["Keywords"].str.strip()
                        freq_dict = (
                            kw_exp.groupby("Keywords")["Size"].sum()
                            .sort_values(ascending=False)
                            .to_dict()
                        )
                        cmap = mcolors.LinearSegmentedColormap.from_list(
                            "apuracao",
                            [PALETTE["border_l"], PALETTE["text2"],
                             PALETTE["accent_soft"], PALETTE["accent"]]
                        )
                        wc = WordCloud(
                            width=900, height=500,
                            background_color=PALETTE["surface"],
                            colormap=cmap,
                            max_words=80,
                            prefer_horizontal=0.8,
                            min_font_size=9,
                            max_font_size=72,
                            collocations=False,
                        ).generate_from_frequencies(freq_dict)

                        fig8, ax8 = plt.subplots(figsize=(12, 6))
                        fig8.patch.set_facecolor(PALETTE["surface"])
                        ax8.set_facecolor(PALETTE["surface"])
                        ax8.imshow(wc, interpolation="bilinear")
                        ax8.axis("off")
                        ax8.set_title("Nuvem de Palavras das Keywords", color=PALETTE["text"])
                        plt.tight_layout(pad=0)

                        st.pyplot(fig8, use_container_width=True)
                        download_fig(fig8, "nuvem_keywords.png")
                        plt.close(fig8)
                    else:
                        st.info("Colunas 'Keywords' e 'Size' não encontradas no arquivo.")
                except Exception as e:
                    st.error(f"Erro ao gerar nuvem de palavras: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

    # Limpar arquivo temporário
    try:
        _os.unlink(filtered_result_file)
    except Exception:
        pass