"""
matplotlib_charts.py — Apuração · Agita Comunicação
Lógica 100% preservada das funções originais.
Tema visual aplicado: paleta roxo/laranja/preto, fundo escuro,
grid sutil, labels legíveis e colormap customizado na wordcloud.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
from wordcloud import WordCloud
import seaborn as sns
import re
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# Paleta — espelha os tokens CSS do dashboard
# ─────────────────────────────────────────────────────────────
_P = {
    "bg":       "#0a0008",
    "surface":  "#1a0d2e",
    "surface2": "#231240",
    "surface3": "#2e1a52",
    "border":   "#3d2466",
    "border_l": "#5a3690",
    "accent":   "#ff6b1a",
    "a_soft":   "#ff8c42",
    "a2":       "#ffb347",
    "text":     "#f5eeff",
    "text2":    "#b094d4",
    "muted":    "#6e4f96",
}

# Sequência categórica: laranja → roxo → âmbar → violeta…
_CAT = [
    "#ff6b1a", "#b094d4", "#ffb347", "#7c4dbd",
    "#ff8c42", "#5a3690", "#e05500", "#9c6bcc",
    "#ffd580", "#3d2466", "#ffcba4", "#2e1a52",
]

# Colormap contínuo roxo-escuro → laranja
_CMAP = LinearSegmentedColormap.from_list(
    "apuracao",
    [_P["surface3"], _P["border_l"], _P["text2"], _P["a_soft"], _P["accent"]]
)

# Colormap para wordcloud (vai do roxo médio ao laranja)
_WC_CMAP = LinearSegmentedColormap.from_list(
    "apuracao_wc",
    [_P["border_l"], _P["text2"], _P["a_soft"], _P["accent"]]
)


def _apply_theme():
    """Aplica o rcParams de tema escuro globalmente antes de criar qualquer fig."""
    plt.rcParams.update({
        "figure.facecolor":  _P["surface"],
        "axes.facecolor":    _P["surface"],
        "axes.edgecolor":    _P["border"],
        "axes.labelcolor":   _P["text2"],
        "axes.titlecolor":   _P["text"],
        "axes.titlesize":    13,
        "axes.titleweight":  "semibold",
        "axes.labelsize":    11,
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.grid":         True,
        "grid.color":        _P["border"],
        "grid.linewidth":    0.5,
        "grid.alpha":        0.5,
        "xtick.color":       _P["muted"],
        "ytick.color":       _P["muted"],
        "xtick.labelsize":   9,
        "ytick.labelsize":   9,
        "text.color":        _P["text"],
        "font.family":       "sans-serif",
        "legend.facecolor":  _P["surface2"],
        "legend.edgecolor":  _P["border"],
        "legend.labelcolor": _P["text2"],
        "legend.fontsize":   9,
        "legend.title_fontsize": 9,
    })


def _finish(fig):
    """Garante fundo e tight_layout em qualquer fig antes de retornar."""
    fig.patch.set_facecolor(_P["surface"])
    for ax in fig.get_axes():
        ax.set_facecolor(_P["surface"])
        for spine in ax.spines.values():
            spine.set_edgecolor(_P["border"])
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────
# focus_pie_chart
# ─────────────────────────────────────────────────────────────
def focus_pie_chart(news_file):
    _apply_theme()

    df = pd.read_csv(news_file)

    focus_series = (
        df["Focus"]
        .dropna()
        .str.split("|")
        .explode()
        .str.strip()
    )

    focus_counts = focus_series.value_counts()
    top10  = focus_counts.head(10)
    others = focus_counts.iloc[10:].sum()
    plot_data = pd.concat([top10, pd.Series({"Outros": others})])

    fig, ax = plt.subplots(figsize=(7, 7))

    # Cores categóricas da paleta
    colors = (_CAT * 3)[: len(plot_data)]

    wedges, texts, autotexts = ax.pie(
        plot_data.values,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.82,
        wedgeprops=dict(linewidth=1.5, edgecolor=_P["surface"]),
    )

    for t in texts:
        t.set_color(_P["text2"])
        t.set_fontsize(0)          # oculta labels externas (legenda já cobre)

    for at in autotexts:
        at.set_color(_P["text"])
        at.set_fontsize(8)
        at.set_fontweight("semibold")

    ax.legend(
        wedges,
        plot_data.index,
        title="Focus",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        framealpha=0.85,
    )

    ax.set_title("Distribuição dos Principais Temas")

    return _finish(fig)


# ─────────────────────────────────────────────────────────────
# focus_bar_chart
# ─────────────────────────────────────────────────────────────
def focus_bar_chart(news_file):
    _apply_theme()

    df = pd.read_csv(news_file)

    focus_series = (
        df["Focus"]
        .dropna()
        .str.split("|")
        .explode()
        .str.strip()
    )

    focus_counts = focus_series.value_counts()
    top10  = focus_counts.head(10)
    others = focus_counts.iloc[10:].sum()
    plot_data = pd.concat([top10, pd.Series({"Outros": others})]).sort_values()

    fig, ax = plt.subplots(figsize=(9, 6))

    # Gradiente de cor: menor valor = roxo, maior = laranja
    n = len(plot_data)
    bar_colors = [_CMAP(i / max(n - 1, 1)) for i in range(n)]

    bars = ax.barh(plot_data.index, plot_data.values, color=bar_colors,
                   edgecolor=_P["surface"], linewidth=0.8, height=0.65)

    for bar in bars:
        w = bar.get_width()
        ax.text(
            w + max(plot_data.values) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{int(w):,}",
            va="center", ha="left",
            color=_P["text2"], fontsize=8,
        )

    ax.set_xlabel("Número de ocorrências")
    ax.set_title("Distribuição dos Principais Temas (Focus)")
    ax.set_xlim(0, plot_data.max() * 1.15)

    return _finish(fig)


# ─────────────────────────────────────────────────────────────
# focus_weighted_importance_chart
# ─────────────────────────────────────────────────────────────
def focus_weighted_importance_chart(news_file):
    _apply_theme()

    df = pd.read_csv(news_file)

    focus_expanded = (
        df[["Focus", "Size"]]
        .dropna()
        .assign(Focus=lambda x: x["Focus"].str.split("|"))
        .explode("Focus")
    )
    focus_expanded["Focus"] = focus_expanded["Focus"].str.strip()

    focus_weighted = (
        focus_expanded
        .groupby("Focus")["Size"]
        .sum()
        .sort_values(ascending=False)
    )

    top30  = focus_weighted.head(30)
    others = focus_weighted.iloc[30:].sum()
    plot_data = pd.concat([top30, pd.Series({"Outros": others})])
    plot_data_pct = (plot_data / plot_data.sum() * 100).sort_values()

    n = len(plot_data_pct)
    bar_colors = [_CMAP(i / max(n - 1, 1)) for i in range(n)]

    fig, ax = plt.subplots(figsize=(9, 6))

    bars = ax.barh(
        plot_data_pct.index, plot_data_pct.values,
        color=bar_colors, edgecolor=_P["surface"], linewidth=0.8, height=0.65,
    )

    for bar in bars:
        w = bar.get_width()
        ax.text(
            w + 0.15,
            bar.get_y() + bar.get_height() / 2,
            f"{w:.1f}%",
            va="center", ha="left",
            color=_P["text2"], fontsize=8,
        )

    ax.set_xlabel("Proporção ponderada (%)")
    ax.set_title("Importância Temática Ponderada por Tamanho do Cluster")
    ax.set_xlim(0, plot_data_pct.max() * 1.15)

    return _finish(fig)


# ─────────────────────────────────────────────────────────────
# temporal_trend_chart
# ─────────────────────────────────────────────────────────────
def temporal_trend_chart(clusters_path, news_file):
    _apply_theme()

    articles_file = Path(clusters_path) / "articles_merged_cleaned_clustered_organized.csv"

    news_df     = pd.read_csv(articles_file)
    clusters_df = pd.read_csv(news_file)

    news_df["publish_date"] = pd.to_datetime(
        news_df["publish_date"], errors="coerce", utc=True
    )
    news_df = news_df.dropna(subset=["publish_date"])
    news_df["publish_date"] = news_df["publish_date"].dt.tz_localize(None)
    news_df = news_df[news_df["publish_date"] >= "2025-11-01"]
    news_df["period"] = news_df["publish_date"]

    merged = news_df.merge(
        clusters_df[["Cluster ID", "Focus"]],
        on="Cluster ID",
        how="left",
    )

    focus_expanded = (
        merged[["period", "Focus"]]
        .dropna()
        .assign(Focus=lambda x: x["Focus"].str.split("|"))
        .explode("Focus")
    )
    focus_expanded["Focus"] = focus_expanded["Focus"].str.strip()

    trend = (
        focus_expanded
        .groupby([pd.Grouper(key="period", freq="7D"), "Focus"])
        .size()
        .reset_index(name="count")
    )

    trend_pivot = trend.pivot(
        index="period", columns="Focus", values="count"
    ).fillna(0).sort_index()

    top_topics  = focus_expanded["Focus"].value_counts().head(6).index
    trend_top   = trend_pivot[top_topics]

    fig, ax = plt.subplots(figsize=(11, 6))

    for i, col in enumerate(trend_top.columns):
        color = _CAT[i % len(_CAT)]
        ax.plot(
            trend_top.index, trend_top[col],
            marker="o", markersize=4,
            linewidth=1.8, label=col,
            color=color,
        )

    ax.set_ylabel("Número de artigos")
    ax.set_xlabel("Tempo")
    ax.set_title("Tendência Temporal dos Principais Temas")
    plt.xticks(rotation=45)

    ax.legend(
        framealpha=0.85,
        bbox_to_anchor=(1.01, 1),
        loc="upper left",
    )

    return _finish(fig)


# ─────────────────────────────────────────────────────────────
# top_sources_chart
# ─────────────────────────────────────────────────────────────
def top_sources_chart(clusters_path):
    _apply_theme()

    articles_file = Path(clusters_path) / "articles_merged_cleaned_clustered_organized.csv"
    df = pd.read_csv(articles_file)

    source_counts = df["source"].value_counts()
    top_sources   = source_counts.head(10).sort_values()

    n = len(top_sources)
    bar_colors = [_CMAP(i / max(n - 1, 1)) for i in range(n)]

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.barh(
        top_sources.index, top_sources.values,
        color=bar_colors, edgecolor=_P["surface"], linewidth=0.8, height=0.65,
    )

    for bar in bars:
        w = bar.get_width()
        ax.text(
            w + max(top_sources.values) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{int(w):,}",
            va="center", ha="left",
            color=_P["text2"], fontsize=8,
        )

    ax.set_xlabel("Número de notícias")
    ax.set_title("Top 10 Fontes de Notícias no Dataset")
    ax.set_xlim(0, top_sources.max() * 1.15)

    return _finish(fig)


# ─────────────────────────────────────────────────────────────
# source_focus_distribution_chart
# ─────────────────────────────────────────────────────────────
def source_focus_distribution_chart(clusters_path, news_file):
    _apply_theme()

    articles_file = Path(clusters_path) / "articles_merged_cleaned_clustered_organized.csv"
    articles_df   = pd.read_csv(articles_file)
    clusters_df   = pd.read_csv(news_file)

    merged = articles_df.merge(
        clusters_df[["Cluster ID", "Focus", "Size"]],
        on="Cluster ID",
        how="left",
    )

    focus_expanded = (
        merged[["source", "Focus", "canonical_url"]]
        .dropna()
        .assign(Focus=lambda x: x["Focus"].str.split("|"))
        .explode("Focus")
    )
    focus_expanded["Focus"] = focus_expanded["Focus"].str.strip()

    top_focus = focus_expanded["Focus"].value_counts().head(5).index

    focus_expanded["Focus_grouped"] = focus_expanded["Focus"].apply(
        lambda x: x if x in top_focus else "Outros"
    )

    source_focus_counts = (
        focus_expanded
        .groupby(["source", "Focus_grouped"])["canonical_url"]
        .nunique()
        .reset_index(name="count")
    )

    top_sources = (
        focus_expanded["source"]
        .value_counts()
        .head(8)
        .index
    )

    filtered = source_focus_counts[source_focus_counts["source"].isin(top_sources)]

    pivot = filtered.pivot(
        index="source", columns="Focus_grouped", values="count"
    ).fillna(0)
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    # Cores das barras empilhadas
    n_cats = len(pivot.columns)
    stack_colors = (_CAT * 3)[:n_cats]

    fig, ax = plt.subplots(figsize=(12, 7))

    pivot.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=stack_colors,
        edgecolor=_P["surface"],
        linewidth=0.6,
    )

    ax.set_xlabel("Fonte")
    ax.set_ylabel("Número de artigos")
    ax.set_title("Distribuição dos Principais Temas por Fonte")
    plt.xticks(rotation=45, ha="right")

    ax.legend(
        title="Focus",
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
        framealpha=0.85,
    )

    return _finish(fig)


# ─────────────────────────────────────────────────────────────
# keyword_weight_chart
# ─────────────────────────────────────────────────────────────
def keyword_weight_chart(clusters_df):
    _apply_theme()

    keywords_expanded = (
        clusters_df[["Keywords", "Size"]]
        .dropna()
        .assign(Keywords=lambda x: x["Keywords"].str.split(";"))
        .explode("Keywords")
    )
    keywords_expanded["Keywords"] = keywords_expanded["Keywords"].str.strip()

    keyword_weight = (
        keywords_expanded
        .groupby("Keywords")["Size"]
        .sum()
        .sort_values(ascending=False)
    )

    top_keywords = keyword_weight.head(20).sort_values()

    n = len(top_keywords)
    bar_colors = [_CMAP(i / max(n - 1, 1)) for i in range(n)]

    fig, ax = plt.subplots(figsize=(10, 7))

    bars = ax.barh(
        top_keywords.index, top_keywords.values,
        color=bar_colors, edgecolor=_P["surface"], linewidth=0.8, height=0.65,
    )

    for bar in bars:
        w = bar.get_width()
        ax.text(
            w + max(top_keywords.values) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{int(w):,}",
            va="center", ha="left",
            color=_P["text2"], fontsize=8,
        )

    ax.set_xlabel("Peso total (soma dos tamanhos dos clusters)")
    ax.set_ylabel("Palavra-chave")
    ax.set_title("Palavras-chave mais relevantes ponderadas pelo tamanho do cluster")
    ax.set_xlim(0, top_keywords.max() * 1.15)

    return _finish(fig)


# ─────────────────────────────────────────────────────────────
# keywords_wordcloud
# ─────────────────────────────────────────────────────────────
def keywords_wordcloud(clusters_df):
    _apply_theme()

    keywords_expanded = (
        clusters_df[["Keywords", "Size"]]
        .dropna()
        .assign(Keywords=lambda x: x["Keywords"].str.split(";"))
        .explode("Keywords")
    )
    keywords_expanded["Keywords"] = keywords_expanded["Keywords"].str.strip()

    keyword_weight = (
        keywords_expanded
        .groupby("Keywords")["Size"]
        .sum()
        .sort_values(ascending=False)
    )

    freq_dict = keyword_weight.to_dict()

    wordcloud = WordCloud(
        width=900,
        height=500,
        background_color=_P["surface"],   # fundo roxo escuro
        colormap=_WC_CMAP,                # roxo → laranja
        max_words=80,
        prefer_horizontal=0.8,
        min_font_size=9,
        max_font_size=72,
        collocations=False,
    ).generate_from_frequencies(freq_dict)

    fig, ax = plt.subplots(figsize=(12, 6))

    fig.patch.set_facecolor(_P["surface"])
    ax.set_facecolor(_P["surface"])
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Nuvem de Palavras das Keywords", color=_P["text"])

    return fig