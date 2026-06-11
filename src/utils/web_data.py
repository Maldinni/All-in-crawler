"""
web_data.py — Apuração · Agita Comunicação

Constrói o objeto de dados (mesma forma do antigo app/data.js) a partir
dos CSVs reais gerados pelo pipeline, para alimentar a nova interface React.

Espelha a lógica de agregação de src/visualizations/matplotlib_charts.py,
mas devolve JSON-serializável em vez de figuras matplotlib.
"""

import math
from pathlib import Path

import pandas as pd

from src.utils.parsing import clean_llm_text
from src.utils.pipeline_runner import PIPELINE_STEPS

# Paleta categórica — espelha os tokens da nova identidade visual (styles.css)
PALETTE = [
    "#FF6A24", "#7C5BE8", "#FF4D6D", "#2DB1A8", "#4D9BFF",
    "#F2B705", "#B06BF2", "#5BD68A", "#FF8A4D", "#9489AD",
    "#9B82F2", "#FFB347",
]

ARTICLES_FILE = "articles_merged_cleaned_clustered_organized.csv"


def _color(i):
    return PALETTE[i % len(PALETTE)]


def _read_csv(path):
    """Lê CSV em UTF-8, com fallback para latin-1."""
    try:
        return pd.read_csv(path, encoding="utf-8")
    except (UnicodeDecodeError, UnicodeError):
        return pd.read_csv(path, encoding="latin-1")


def _truncate(text, n):
    text = str(text).strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


# ─────────────────────────────────────────────────────────────
# Etapas do pipeline (deriva dos PIPELINE_STEPS reais)
# ─────────────────────────────────────────────────────────────
def build_pipeline_steps():
    steps = []
    for i, (step_name, script_path) in enumerate(PIPELINE_STEPS, start=1):
        # "Step 2 — Cleaning"  ->  id=2, label="Cleaning"
        label = step_name
        num = i
        if "—" in step_name:
            left, right = step_name.split("—", 1)
            label = right.strip()
            digits = "".join(c for c in left if c.isdigit())
            if digits:
                num = int(digits)
        steps.append({
            "id": num,
            "label": label,
            "sub": Path(str(script_path)).name,
        })
    return steps


# ─────────────────────────────────────────────────────────────
# Distribuição de temas (Focus)  — espelha focus_pie/bar_chart
# ─────────────────────────────────────────────────────────────
def build_focus_counts(clusters_df, top=10):
    focus_series = (
        clusters_df["Focus"]
        .dropna()
        .str.split("|")
        .explode()
        .str.strip()
    )
    counts = focus_series.value_counts()
    top_n = counts.head(top)
    others = counts.iloc[top:].sum()

    out = []
    for i, (name, value) in enumerate(top_n.items()):
        out.append({"name": name, "value": int(value), "color": _color(i)})
    if others > 0:
        out.append({"name": "Outros", "value": int(others), "color": PALETTE[9]})
    return out


def _focus_color_map(focus_counts):
    return {f["name"]: f["color"] for f in focus_counts}


# ─────────────────────────────────────────────────────────────
# Palavras-chave ponderadas — espelha keyword_weight_chart
# ─────────────────────────────────────────────────────────────
def build_keywords(clusters_df, top=10):
    kw = (
        clusters_df[["Keywords", "Size"]]
        .dropna()
        .assign(Keywords=lambda x: x["Keywords"].str.split(";"))
        .explode("Keywords")
    )
    kw["Keywords"] = kw["Keywords"].str.strip()
    kw = kw[kw["Keywords"] != ""]

    weight = kw.groupby("Keywords")["Size"].sum().sort_values(ascending=False)
    top_n = weight.head(top)

    out = []
    n = len(top_n)
    for i, (name, value) in enumerate(top_n.items()):
        # gradiente laranja -> roxo
        out.append({"name": name, "value": int(value), "color": _color(i)})
    return out


# ─────────────────────────────────────────────────────────────
# Fontes — espelha top_sources_chart
# ─────────────────────────────────────────────────────────────
def build_fontes(articles_df, top=10):
    if articles_df is None or "source" not in articles_df.columns:
        return []
    counts = articles_df["source"].value_counts().head(top)
    return [
        {"name": str(name), "value": int(value), "color": _color(i)}
        for i, (name, value) in enumerate(counts.items())
    ]


# ─────────────────────────────────────────────────────────────
# Tendência temporal — espelha temporal_trend_chart
# ─────────────────────────────────────────────────────────────
def build_trend(articles_df, clusters_df, top_topics=6):
    empty = {"labels": [], "series": []}
    if articles_df is None or "publish_date" not in articles_df.columns:
        return empty

    df = articles_df.copy()
    df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce", utc=True)
    df = df.dropna(subset=["publish_date"])
    if df.empty:
        return empty
    df["publish_date"] = df["publish_date"].dt.tz_localize(None)
    df = df[df["publish_date"] >= "2025-11-01"]
    df["period"] = df["publish_date"]

    merged = df.merge(
        clusters_df[["Cluster ID", "Focus"]], on="Cluster ID", how="left"
    )

    focus_expanded = (
        merged[["period", "Focus"]]
        .dropna()
        .assign(Focus=lambda x: x["Focus"].str.split("|"))
        .explode("Focus")
    )
    focus_expanded["Focus"] = focus_expanded["Focus"].str.strip()
    if focus_expanded.empty:
        return empty

    grouped = (
        focus_expanded
        .groupby([pd.Grouper(key="period", freq="7D"), "Focus"])
        .size()
        .reset_index(name="count")
    )
    pivot = (
        grouped.pivot(index="period", columns="Focus", values="count")
        .fillna(0)
        .sort_index()
    )

    top = focus_expanded["Focus"].value_counts().head(top_topics).index.tolist()
    pivot = pivot[top]

    labels = [d.strftime("%d/%m") for d in pivot.index]
    series = []
    for i, col in enumerate(top):
        series.append({
            "name": col,
            "color": _color(i),
            "points": [int(v) for v in pivot[col].tolist()],
        })
    return {"labels": labels, "series": series}


# ─────────────────────────────────────────────────────────────
# Tabela de clusters
# ─────────────────────────────────────────────────────────────
def build_clusters(clusters_df, focus_color):
    rows = []
    for _, r in clusters_df.iterrows():
        keywords = [
            k.strip() for k in str(r.get("Keywords", "") or "").split(";") if k.strip()
        ]
        focus_raw = str(r.get("Focus", "") or "").strip()
        focus_first = focus_raw.split("|")[0].strip() if focus_raw else "—"

        try:
            similarity = float(r.get("Similarity", 0) or 0)
        except (ValueError, TypeError):
            similarity = 0.0
        if math.isnan(similarity):
            similarity = 0.0

        def _int(v, default=0):
            try:
                return int(float(v))
            except (ValueError, TypeError):
                return default

        rows.append({
            "id": _int(r.get("Cluster ID")),
            "title": str(r.get("Title", "") or "").strip(),
            "size": _int(r.get("Size")),
            "keywords": keywords,
            "description": _truncate(r.get("Description", ""), 240),
            "focus": _truncate(focus_first, 48) if focus_first else "—",
            "focusColor": focus_color.get(focus_first, "#9489AD"),
            "similar": _int(r.get("Most Similar Cluster")),
            "similarity": round(similarity, 2),
            "distinguishing": _truncate(r.get("Distinguishing Features", ""), 160),
            "trend": _truncate(clean_llm_text(str(r.get("Trends", "") or "")), 90),
        })
    return rows


# ─────────────────────────────────────────────────────────────
# Builder principal
# ─────────────────────────────────────────────────────────────
def build_app_data(result_file, processed_path):
    """Devolve um dict JSON-serializável com os dados reais do pipeline.

    Se os arquivos não existirem, devolve hasData=False com listas vazias —
    a interface mostra os estados vazios ("Execute o pipeline primeiro").
    """
    pipeline_steps = build_pipeline_steps()
    result_path = Path(result_file)

    if not result_path.exists():
        return {
            "hasData": False,
            "pipelineSteps": pipeline_steps,
            "stats": {"total": 0, "clusters": 0, "fontes": 0, "colunas": 0},
            "clusters": [],
            "focusCounts": [],
            "fontes": [],
            "keywords": [],
            "trend": {"labels": [], "series": []},
        }

    clusters_df = _read_csv(result_path)

    articles_path = Path(processed_path) / ARTICLES_FILE
    articles_df = _read_csv(articles_path) if articles_path.exists() else None

    focus_counts = build_focus_counts(clusters_df)
    focus_color = _focus_color_map(focus_counts)

    stats = {
        "total": int(len(articles_df)) if articles_df is not None else int(len(clusters_df)),
        "clusters": int(clusters_df["Cluster ID"].nunique())
        if "Cluster ID" in clusters_df.columns else int(len(clusters_df)),
        "fontes": int(articles_df["source"].nunique())
        if (articles_df is not None and "source" in articles_df.columns) else 0,
        "colunas": int(len(clusters_df.columns)),
    }

    return {
        "hasData": True,
        "pipelineSteps": pipeline_steps,
        "stats": stats,
        "clusters": build_clusters(clusters_df, focus_color),
        "focusCounts": focus_counts,
        "fontes": build_fontes(articles_df),
        "keywords": build_keywords(clusters_df),
        "trend": build_trend(articles_df, clusters_df),
    }
