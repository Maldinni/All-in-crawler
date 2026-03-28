import os
import time
import streamlit as st
import pandas as pd
from src.utils.io import ensure_dirs
from src.utils.parsing import parse_args, load_config
from src.utils.pipeline_runner import run_pipeline, PIPELINE_STEPS
from src.utils.data_loader import load_results, search_dataframe
from src.visualizations.matplotlib_charts import (
    focus_pie_chart,
    focus_bar_chart,
    keywords_wordcloud,
    focus_weighted_importance_chart,
    temporal_trend_chart,
    top_sources_chart,
    source_focus_distribution_chart,
    keyword_weight_chart
)

# ─────────────────────────────────────────────
# Config & Paths (lógica preservada)
# ─────────────────────────────────────────────
args = parse_args()
cfg = load_config(args)

paths = cfg["paths"]
ensure_dirs(paths["raw"], paths["processed"], paths["checkpoints"], paths["output"])

path = f'{cfg["paths"]["processed"]}'

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
# Global CSS — 60/30/10: Roxo · Laranja · Preto
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
    --purple-glow:   rgba(124,60,210,0.18);
    --accent:        #ff6b1a;
    --accent-dim:    rgba(255,107,26,0.15);
    --accent-soft:   #ff8c42;
    --accent-2:      #ffb347;
    --text-primary:  #f5eeff;
    --text-secondary:#b094d4;
    --text-muted:    #6e4f96;
    --success:       #ff6b1a;
    --danger:        #ff3d6b;
    --warn:          #ffb347;
    --radius:        10px;
    --radius-lg:     16px;
    --shadow:        0 1px 4px rgba(0,0,0,.6), 0 4px 20px rgba(10,0,20,.5);
    --shadow-lg:     0 2px 10px rgba(0,0,0,.7), 0 12px 48px rgba(10,0,20,.6);
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

.block-container {
    padding: 2rem 2.5rem 4rem !important;
    max-width: 1280px !important;
}

h1, h2, h3, h4 {
    font-family: var(--font) !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
    color: var(--text-primary) !important;
}
p, li, span, label, div { font-family: var(--font) !important; color: var(--text-primary); }

[data-testid="stSidebar"] .stRadio label {
    font-size: 0.875rem !important;
    color: var(--text-secondary) !important;
    padding: 0.45rem 0.75rem !important;
    border-radius: 6px !important;
    transition: background 0.15s, color 0.15s !important;
    cursor: pointer;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: var(--surface-2) !important;
    color: var(--text-primary) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent-soft)) !important;
    color: #0a0008 !important;
    font-family: var(--font) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    border: none !important;
    border-radius: var(--radius) !important;
    padding: 0.6rem 1.4rem !important;
    cursor: pointer !important;
    transition: opacity 0.15s, transform 0.1s !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover  { opacity: 0.88 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }
.stButton > button:disabled {
    background: var(--surface-2) !important;
    color: var(--text-muted) !important;
    cursor: not-allowed !important;
    opacity: 0.5 !important;
}

.stTextInput > div > div > input {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
    font-family: var(--font) !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 0.9rem !important;
    transition: border-color 0.15s !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-dim) !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
}

[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--accent), var(--accent-2)) !important;
    border-radius: 9999px !important;
}
[data-testid="stProgressBar"] > div {
    background: var(--surface-2) !important;
    border-radius: 9999px !important;
}

[data-testid="stMetric"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.1rem 1.4rem !important;
    box-shadow: var(--shadow) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stMetric"]:hover {
    border-color: var(--accent) !important;
    box-shadow: var(--shadow), 0 0 18px var(--accent-dim) !important;
}
[data-testid="stMetricLabel"] { color: var(--text-secondary) !important; font-size: 0.8rem !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.06em; }
[data-testid="stMetricValue"] { color: var(--accent-soft) !important; font-size: 1.7rem !important; font-weight: 600 !important; }
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

[data-testid="stTabs"] [role="tablist"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 3px !important;
    gap: 2px !important;
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 7px !important;
    font-family: var(--font) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    padding: 0.4rem 1rem !important;
    border: none !important;
    transition: background 0.15s, color 0.15s !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: var(--surface-3) !important;
    color: var(--accent-soft) !important;
    box-shadow: inset 0 0 0 1px var(--border-light) !important;
}

[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--font) !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
}

[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    background: var(--surface-2) !important;
    font-size: 0.875rem !important;
}

[data-testid="stImage"], .stPyplot {
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 99px; }

hr { border-color: var(--border) !important; }

/* Sidebar logo */
[data-testid="stSidebar"] [data-testid="stImage"] {
    display: block !important;
    margin: 0 auto !important;
    filter: brightness(0) invert(1) sepia(1) saturate(3) hue-rotate(310deg) brightness(1.1) !important;
}
[data-testid="stSidebar"] [data-testid="stImage"] img { border-radius: 0 !important; }

.nt-section-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    font-weight: 600;
    margin: 0 0 0.6rem;
}

.nt-page-header {
    margin-bottom: 2rem;
    padding-bottom: 1.25rem;
    border-bottom: 1px solid var(--border);
    position: relative;
}
.nt-page-header::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0;
    width: 64px; height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    border-radius: 9999px;
}
.nt-page-header h1 { font-size: 1.6rem !important; margin: 0 !important; }
.nt-page-header p  { color: var(--text-secondary); font-size: 0.9rem; margin: 0.3rem 0 0; }

.nt-step-running { color: var(--accent-soft); font-size:0.85rem; font-weight:500; }
.nt-step-done    { color: var(--accent);       font-size:0.85rem; font-weight:500; }
.nt-step-pending { color: var(--text-muted);   font-size:0.85rem; }

.nt-log {
    height: 360px;
    overflow-y: auto;
    background: var(--bg-pure);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1rem 1.2rem;
    font-family: var(--mono);
    font-size: 0.78rem;
    line-height: 1.7;
    color: var(--accent-soft);
}

.nt-chart-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow);
    transition: border-color 0.2s;
}
.nt-chart-wrap:hover { border-color: var(--border-light); }
.nt-chart-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--accent-soft);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 1rem;
    padding-left: 0.6rem;
    border-left: 2px solid var(--accent);
}

/* ── Página Sobre ── */
.ap-hero {
    background: linear-gradient(135deg, var(--surface-2) 0%, var(--surface-3) 100%);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: 2.5rem 2rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.ap-hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(255,107,26,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.ap-hero-tag {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--accent);
    border: 1px solid var(--accent-dim);
    background: rgba(255,107,26,0.08);
    border-radius: 99px;
    padding: 0.2rem 0.75rem;
    margin-bottom: 1rem;
}
.ap-hero h2 {
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    margin: 0 0 0.6rem !important;
    line-height: 1.2 !important;
}
.ap-hero p {
    color: var(--text-secondary) !important;
    font-size: 1rem;
    max-width: 640px;
    line-height: 1.7;
    margin: 0 !important;
}

.ap-feature-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.4rem;
    height: 100%;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.ap-feature-card:hover {
    border-color: var(--accent);
    box-shadow: 0 0 20px var(--accent-dim);
}
.ap-feature-icon  { font-size: 1.5rem; margin-bottom: 0.75rem; display: block; }
.ap-feature-title { font-size: 0.95rem !important; font-weight: 600 !important; color: var(--text-primary) !important; margin: 0 0 0.4rem !important; }
.ap-feature-desc  { font-size: 0.82rem !important; color: var(--text-secondary) !important; line-height: 1.6 !important; margin: 0 !important; }

.ap-step-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.4rem 1.4rem 1.4rem 1.1rem;
    border-left: 3px solid var(--accent);
    height: 100%;
}
.ap-step-number { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--accent); margin-bottom: 0.4rem; }
.ap-step-title  { font-size: 0.9rem !important; font-weight: 600 !important; color: var(--text-primary) !important; margin: 0 0 0.3rem !important; }
.ap-step-desc   { font-size: 0.8rem !important; color: var(--text-secondary) !important; line-height: 1.55 !important; margin: 0 !important; }

.ap-usecase-card  { background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 1.25rem; }
.ap-usecase-title { font-size: 0.85rem !important; font-weight: 700 !important; color: var(--accent-soft) !important; text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 0.75rem !important; }
.ap-usecase-item  { font-size: 0.82rem !important; color: var(--text-secondary) !important; padding: 0.2rem 0; display: flex; gap: 0.4rem; align-items: flex-start; line-height: 1.5; }

.ap-section-title { font-size: 1.1rem !important; font-weight: 700 !important; color: var(--text-primary) !important; margin: 0 0 0.25rem !important; letter-spacing: -0.01em !important; }
.ap-section-sub   { font-size: 0.85rem !important; color: var(--text-secondary) !important; margin: 0 0 1.5rem !important; }
.ap-divider       { border: none; border-top: 1px solid var(--border); margin: 2rem 0; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Sidebar — Logo + Navegação
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("D:\github\All-in-crawler\logoofcapudados.png", width=160)
    st.markdown('<hr style="border-color:var(--border);margin:0.75rem 0 1rem">', unsafe_allow_html=True)

    st.markdown('<p class="nt-section-label">Navegação</p>', unsafe_allow_html=True)

    page = st.radio(
        label="nav",
        options=["Sobre", "Executar Pipeline", "Resultados", "Visualizações"],
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:0 0.5rem">
        <p style="font-size:0.72rem;color:#6e4f96;line-height:1.6">
            Plataforma de inteligência de narrativas da
            <span style="color:#b094d4;font-weight:600">Agita Comunicação</span>.
            Análise semântica e identificação de tendências em tempo real.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Página: Sobre
# ─────────────────────────────────────────────
if page == "Sobre":

    # Hero banner
    st.markdown("""
    <div class="ap-hero">
        <span class="ap-hero-tag">Agita Comunicação · Plataforma</span>
        <h2>Inteligência de Narrativas<br>para o Debate Público</h2>
        <p>
            O Apuração transforma grandes volumes de dados digitais em insights
            estratégicos e acionáveis — identificando tendências emergentes antes mesmo
            de chegarem à grande mídia.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Dimensões de análise ──
    st.markdown('<p class="ap-section-title">Dimensões de Análise</p>', unsafe_allow_html=True)
    st.markdown('<p class="ap-section-sub">O que a plataforma monitora e classifica em tempo real</p>', unsafe_allow_html=True)

    d1, d2, d3, d4, d5 = st.columns(5, gap="small")
    dims = [
        ("📈", "Tendências",    "Temas que estão ganhando ou perdendo relevância no debate público."),
        ("🗣️", "Narrativas",   "Como os assuntos são construídos e disseminados pelo público."),
        ("💬", "Tom Emocional", "Sentimento predominante e reações nas discussões digitais."),
        ("⚖️", "Viés Político", "Posicionamentos ideológicos e grau de polarização."),
        ("👤", "Atores",        "Perfis e organizações que lideram e impulsionam o debate."),
    ]
    for col, (icon, title, desc) in zip([d1, d2, d3, d4, d5], dims):
        with col:
            st.markdown(f"""
            <div class="ap-feature-card">
                <span class="ap-feature-icon">{icon}</span>
                <p class="ap-feature-title">{title}</p>
                <p class="ap-feature-desc">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<hr class="ap-divider">', unsafe_allow_html=True)

    # ── Como funciona ──
    st.markdown('<p class="ap-section-title">Como Funciona</p>', unsafe_allow_html=True)
    st.markdown('<p class="ap-section-sub">Pipeline de 4 etapas — da coleta ao insight</p>', unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4, gap="medium")
    pipeline_steps = [
        ("01", "Coleta de Dados",     "Monitoramento abrangente de notícias, redes sociais e conteúdos digitais públicos em tempo real."),
        ("02", "Ciência de Dados",    "Tratamento, organização e identificação de padrões complexos em grandes volumes de informação."),
        ("03", "IA Proprietária",     "Análise semântica e classificação de narrativas com modelos exclusivos desenvolvidos pela Agita."),
        ("04", "Extração de Insights","Tradução de dados complexos em informações claras e acionáveis para suporte à decisão."),
    ]
    for col, (num, title, desc) in zip([s1, s2, s3, s4], pipeline_steps):
        with col:
            st.markdown(f"""
            <div class="ap-step-card">
                <p class="ap-step-number">Etapa {num}</p>
                <p class="ap-step-title">{title}</p>
                <p class="ap-step-desc">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<hr class="ap-divider">', unsafe_allow_html=True)

    # ── Casos de uso ──
    st.markdown('<p class="ap-section-title">Casos de Uso</p>', unsafe_allow_html=True)
    st.markdown('<p class="ap-section-sub">Quem usa e para quê</p>', unsafe_allow_html=True)

    u1, u2, u3, u4 = st.columns(4, gap="medium")
    usecases = [
        ("📰 Jornalismo", [
            "Identificação de pautas emergentes",
            "Análise de tendências sociais",
            "Monitoramento de debates relevantes",
        ]),
        ("🗳️ Política", [
            "Acompanhamento de narrativas eleitorais",
            "Análise de polarização",
            "Monitoramento de opinião pública",
        ]),
        ("🏢 Empresas", [
            "Monitoramento de reputação",
            "Identificação precoce de crises",
            "Análise de percepção pública",
        ]),
        ("📣 Influenciadores", [
            "Descoberta de tendências",
            "Identificação de temas em ascensão",
            "Engajamento com narrativas virais",
        ]),
    ]
    for col, (title, items) in zip([u1, u2, u3, u4], usecases):
        with col:
            items_html = "".join(
                f'<div class="ap-usecase-item">'
                f'<span style="color:var(--accent);margin-top:2px">›</span>{item}</div>'
                for item in items
            )
            st.markdown(f"""
            <div class="ap-usecase-card">
                <p class="ap-usecase-title">{title}</p>
                {items_html}
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<hr class="ap-divider">', unsafe_allow_html=True)

    # ── Diferenciais + Insights (duas colunas) ──
    col_diff, col_insights = st.columns([1, 1], gap="large")

    with col_diff:
        st.markdown('<p class="ap-section-title">Diferencial Tecnológico</p>', unsafe_allow_html=True)
        st.markdown('<p class="ap-section-sub">Por que o Apuração é único</p>', unsafe_allow_html=True)
        diffs = [
            ("🧠", "IA Proprietária",       "Modelos desenvolvidos especificamente para análise de narrativas e opinião pública, garantindo precisão contextual."),
            ("⚡", "Escalabilidade",         "Construída para processar grandes volumes de dados sociais complexos em tempo real."),
            ("🔍", "Controle Metodológico", "Metodologias e algoritmos auditáveis, garantindo resultados confiáveis e transparentes."),
            ("🔒", "Independência",          "Livre de dependência de modelos comerciais externos."),
        ]
        for icon, title, desc in diffs:
            st.markdown(f"""
            <div class="ap-feature-card" style="margin-bottom:0.75rem;display:flex;
                 gap:0.9rem;align-items:flex-start;padding:1rem 1.2rem">
                <span style="font-size:1.2rem;flex-shrink:0;margin-top:2px">{icon}</span>
                <div>
                    <p class="ap-feature-title" style="margin-bottom:0.2rem!important">{title}</p>
                    <p class="ap-feature-desc">{desc}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_insights:
        st.markdown('<p class="ap-section-title">Insights Estratégicos</p>', unsafe_allow_html=True)
        st.markdown('<p class="ap-section-sub">O que você ganha com a plataforma</p>', unsafe_allow_html=True)
        insights = [
            ("⏩", "Antecipação",   "Posicione-se à frente do debate antes que as tendências cheguem à grande mídia."),
            ("🎯", "Público",       "Compreensão profunda das mudanças de humor e interesse do seu público-alvo."),
            ("📡", "Influenciadores","Identificação precisa dos atores que realmente impactam sua narrativa."),
            ("⏱️", "Tempo Real",    "Acompanhamento contínuo para ajustes rápidos em estratégias de comunicação."),
            ("📊", "Decisões",      "Tomada de decisões baseada em dados concretos, reduzindo riscos e incertezas."),
        ]
        for icon, title, desc in insights:
            st.markdown(f"""
            <div class="ap-feature-card" style="margin-bottom:0.75rem;display:flex;
                 gap:0.9rem;align-items:flex-start;padding:1rem 1.2rem">
                <span style="font-size:1.2rem;flex-shrink:0;margin-top:2px">{icon}</span>
                <div>
                    <p class="ap-feature-title" style="margin-bottom:0.2rem!important">{title}</p>
                    <p class="ap-feature-desc">{desc}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<hr class="ap-divider">', unsafe_allow_html=True)

    # ── Relatórios ──
    st.markdown('<p class="ap-section-title">Relatórios e Análises</p>', unsafe_allow_html=True)
    st.markdown('<p class="ap-section-sub">Formatos de entrega disponíveis</p>', unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4, gap="medium")
    reports = [
        ("📋", "Tendências",      "Visão macro sobre o que está por vir no cenário digital e debates emergentes."),
        ("🗺️", "Narrativas",     "Estudo detalhado sobre a construção, disseminação e impacto de discursos públicos."),
        ("📡", "Monitoramento",   "Acompanhamento contínuo de temas sensíveis e críticos para a reputação do cliente."),
        ("📄", "Personalizados",  "Documentos formatados sob demanda para suporte à tomada de decisão executiva."),
    ]
    for col, (icon, title, desc) in zip([r1, r2, r3, r4], reports):
        with col:
            st.markdown(f"""
            <div class="ap-step-card">
                <p class="ap-step-number">{icon}</p>
                <p class="ap-step-title">{title}</p>
                <p class="ap-step-desc">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Rodapé / CTA ──
    st.markdown("""
    <div style="background:var(--surface-2);border:1px solid var(--border-light);
                border-radius:var(--radius-lg);padding:1.75rem 2rem;
                text-align:center;margin-top:1rem">
        <p style="font-size:1rem;font-weight:700;color:var(--text-primary);margin:0 0 0.4rem">
            Agita Comunicação
        </p>
        <p style="font-size:0.85rem;color:var(--text-secondary);margin:0 0 0.25rem">
            Agência dedicada à análise de informação, comunicação estratégica e inteligência de dados de alto impacto.
        </p>
        <p style="font-size:0.82rem;color:var(--text-muted);margin:0">
            Para saber mais ou solicitar uma demonstração, entre em contato com a Agita Comunicação.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Página: Executar Pipeline
# ─────────────────────────────────────────────
elif page == "Executar Pipeline":

    st.markdown("""
    <div class="nt-page-header">
        <h1>Executar Pipeline</h1>
        <p>Inicie o pipeline completo de análise para gerar clusters e tendências atualizadas.</p>
    </div>
    """, unsafe_allow_html=True)

    step_status = {name: "pending" for name, _ in PIPELINE_STEPS}

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run_button = st.button(
            "▶  Iniciar Pipeline",
            disabled=st.session_state.get("running", False),
            use_container_width=True
        )

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


# ─────────────────────────────────────────────
# Página: Resultados
# ─────────────────────────────────────────────
elif page == "Resultados":

    st.markdown("""
    <div class="nt-page-header">
        <h1>Resultados dos Clusters</h1>
        <p>Navegue, pesquise e inspecione os dados de clusters gerados pelo pipeline.</p>
    </div>
    """, unsafe_allow_html=True)

    if not result_file:
        st.warning("Nenhum resultado encontrado. Execute o pipeline primeiro.")
        st.stop()

    df = load_results(result_file)

    total_rows      = len(df)
    total_cols      = len(df.columns)
    unique_clusters = df["cluster"].nunique() if "cluster" in df.columns else "—"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Registros", f"{total_rows:,}")
    m2.metric("Colunas", total_cols)
    m3.metric("Clusters Únicos", unique_clusters)
    m4.metric("Fonte", "Processado")

    st.markdown("<br>", unsafe_allow_html=True)

    keyword = st.text_input(
        label="busca",
        placeholder="🔍  Buscar palavra-chave em todas as colunas…",
        label_visibility="collapsed"
    )

    filtered_df = search_dataframe(df, keyword)

    st.markdown(
        f'<p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:0.5rem">'
        f'{len(filtered_df):,} resultado{"s" if len(filtered_df) != 1 else ""}'
        f'{"  ·  filtrado de " + str(total_rows) if keyword else ""}'
        f'</p>',
        unsafe_allow_html=True
    )

    st.dataframe(filtered_df, use_container_width=True, height=480)


# ─────────────────────────────────────────────
# Página: Visualizações
# ─────────────────────────────────────────────
elif page == "Visualizações":

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

    load_charts = st.button("Carregar Gráficos", use_container_width=False)

    if load_charts:

        with st.spinner("Renderizando visualizações…"):

            tab1, tab2, tab3, tab4 = st.tabs([
                "  Distribuição  ",
                "  Tendências  ",
                "  Fontes  ",
                "  Palavras-chave  "
            ])

            with tab1:
                st.markdown("<br>", unsafe_allow_html=True)
                c_left, c_right = st.columns(2, gap="large")

                with c_left:
                    st.markdown('<div class="nt-chart-wrap"><p class="nt-chart-title">Distribuição de Temas</p>', unsafe_allow_html=True)
                    fig1 = focus_pie_chart(result_file)
                    st.pyplot(fig1)
                    st.markdown('</div>', unsafe_allow_html=True)

                with c_right:
                    st.markdown('<div class="nt-chart-wrap"><p class="nt-chart-title">Frequência de Temas</p>', unsafe_allow_html=True)
                    fig2 = focus_bar_chart(result_file)
                    st.pyplot(fig2)
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="nt-chart-wrap"><p class="nt-chart-title">Importância Ponderada por Cluster</p>', unsafe_allow_html=True)
                fig3 = focus_weighted_importance_chart(result_file)
                st.pyplot(fig3)
                st.markdown('</div>', unsafe_allow_html=True)

            with tab2:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="nt-chart-wrap"><p class="nt-chart-title">Tendência Temporal dos Principais Temas</p>', unsafe_allow_html=True)
                fig4 = temporal_trend_chart(cfg["paths"]["processed"], result_file)
                st.pyplot(fig4)
                st.markdown('</div>', unsafe_allow_html=True)

            with tab3:
                st.markdown("<br>", unsafe_allow_html=True)
                c_left2, c_right2 = st.columns(2, gap="large")

                with c_left2:
                    st.markdown('<div class="nt-chart-wrap"><p class="nt-chart-title">Top 10 Fontes</p>', unsafe_allow_html=True)
                    fig5 = top_sources_chart(cfg["paths"]["processed"])
                    st.pyplot(fig5)
                    st.markdown('</div>', unsafe_allow_html=True)

                with c_right2:
                    st.markdown('<div class="nt-chart-wrap"><p class="nt-chart-title">Distribuição de Temas por Fonte</p>', unsafe_allow_html=True)
                    fig6 = source_focus_distribution_chart(cfg["paths"]["processed"], result_file)
                    st.pyplot(fig6)
                    st.markdown('</div>', unsafe_allow_html=True)

            with tab4:
                st.markdown("<br>", unsafe_allow_html=True)
                c_left3, c_right3 = st.columns(2, gap="large")

                with c_left3:
                    st.markdown('<div class="nt-chart-wrap"><p class="nt-chart-title">Palavras-chave por Peso</p>', unsafe_allow_html=True)
                    fig7 = keyword_weight_chart(clusters_df)
                    st.pyplot(fig7)
                    st.markdown('</div>', unsafe_allow_html=True)

                with c_right3:
                    st.markdown('<div class="nt-chart-wrap"><p class="nt-chart-title">Nuvem de Palavras-chave</p>', unsafe_allow_html=True)
                    fig8 = keywords_wordcloud(clusters_df)
                    st.pyplot(fig8)
                    st.markdown('</div>', unsafe_allow_html=True)