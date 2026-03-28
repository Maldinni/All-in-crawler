import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import seaborn as sns
import re
from pathlib import Path


def focus_pie_chart(news_file):

    df = pd.read_csv(news_file)

    focus_series = (
        df["Focus"]
        .dropna()
        .str.split("|")
        .explode()
        .str.strip()
    )

    focus_counts = focus_series.value_counts()

    top10 = focus_counts.head(10)
    others = focus_counts.iloc[10:].sum()

    plot_data = pd.concat([top10, pd.Series({"Outros": others})])

    fig, ax = plt.subplots(figsize=(7,7))

    colors = plt.cm.tab20(np.linspace(0, 1, len(plot_data)))

    wedges, texts, autotexts = ax.pie(
        plot_data.values,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90
    )

    ax.legend(
        wedges,
        plot_data.index,
        title="Focus",
        loc="center left",
        bbox_to_anchor=(1, 0.5)
    )

    ax.set_title("Distribuição dos Principais Temas")

    return fig


def focus_bar_chart(news_file):

    df = pd.read_csv(news_file)

    focus_series = (
        df["Focus"]
        .dropna()
        .str.split("|")
        .explode()
        .str.strip()
    )

    focus_counts = focus_series.value_counts()

    top10 = focus_counts.head(10)
    others = focus_counts.iloc[10:].sum()

    plot_data = pd.concat([top10, pd.Series({"Outros": others})])
    plot_data = plot_data.sort_values()

    fig, ax = plt.subplots(figsize=(9,6))

    colors = plt.cm.tab20(np.linspace(0, 1, len(plot_data)))

    bars = ax.barh(plot_data.index, plot_data.values, color=colors)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 1,
                bar.get_y() + bar.get_height()/2,
                f'{int(width)}',
                va='center')

    ax.set_xlabel("Número de ocorrências")
    ax.set_title("Distribuição dos Principais Temas (Focus)")

    return fig

def focus_weighted_importance_chart(news_file):

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

    top30 = focus_weighted.head(30)

    others = focus_weighted.iloc[30:].sum()

    plot_data = pd.concat([top30, pd.Series({"Outros": others})])

    plot_data_pct = plot_data / plot_data.sum() * 100
    plot_data_pct = plot_data_pct.sort_values()

    colors = plt.cm.tab20(np.linspace(0, 1, len(plot_data_pct)))

    fig, ax = plt.subplots(figsize=(9,6))

    bars = ax.barh(plot_data_pct.index, plot_data_pct.values, color=colors)

    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.3,
            bar.get_y() + bar.get_height()/2,
            f'{width:.1f}%',
            va='center'
        )

    ax.set_xlabel("Proporção ponderada (%)")
    ax.set_title("Importância Temática Ponderada por Tamanho do Cluster")

    plt.tight_layout()

    return fig

def temporal_trend_chart(clusters_path, news_file):

    articles_file = Path(clusters_path) / "articles_merged_cleaned_clustered_organized.csv"

    news_df = pd.read_csv(articles_file)
    clusters_df = pd.read_csv(news_file)

    # converter datas
    news_df["publish_date"] = pd.to_datetime(
        news_df["publish_date"],
        errors="coerce",
        utc=True
    )

    news_df = news_df.dropna(subset=["publish_date"])

    news_df["publish_date"] = news_df["publish_date"].dt.tz_localize(None)

    news_df = news_df[news_df["publish_date"] >= "2025-11-01"]

    news_df["period"] = news_df["publish_date"]

    merged = news_df.merge(
        clusters_df[["Cluster ID", "Focus"]],
        on="Cluster ID",
        how="left"
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
        index="period",
        columns="Focus",
        values="count"
    ).fillna(0)

    trend_pivot = trend_pivot.sort_index()

    top_topics = focus_expanded["Focus"].value_counts().head(6).index

    trend_top = trend_pivot[top_topics]

    fig, ax = plt.subplots(figsize=(11,6))

    for col in trend_top.columns:
        ax.plot(trend_top.index, trend_top[col], marker="o", label=col)

    ax.set_ylabel("Número de artigos")
    ax.set_xlabel("Tempo")
    ax.set_title("Tendência Temporal dos Principais Temas")

    plt.xticks(rotation=45)

    ax.legend()

    plt.tight_layout()

    return fig

def top_sources_chart(clusters_path):

    articles_file = Path(clusters_path) / "articles_merged_cleaned_clustered_organized.csv"

    df = pd.read_csv(articles_file)

    source_counts = df["source"].value_counts()

    top_sources = source_counts.head(10).sort_values()

    fig, ax = plt.subplots(figsize=(10,6))

    bars = ax.barh(top_sources.index, top_sources.values)

    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 5,
            bar.get_y() + bar.get_height()/2,
            f"{int(width)}",
            va="center"
        )

    ax.set_xlabel("Número de notícias")
    ax.set_title("Top 10 Fontes de Notícias no Dataset")

    plt.tight_layout()

    return fig

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def source_focus_distribution_chart(clusters_path, news_file):

    articles_file = Path(clusters_path) / "articles_merged_cleaned_clustered_organized.csv"

    articles_df = pd.read_csv(articles_file)
    clusters_df = pd.read_csv(news_file)

    merged = articles_df.merge(
        clusters_df[["Cluster ID", "Focus", "Size"]],
        on="Cluster ID",
        how="left"
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

    filtered = source_focus_counts[
        source_focus_counts["source"].isin(top_sources)
    ]

    pivot = filtered.pivot(
        index="source",
        columns="Focus_grouped",
        values="count"
    ).fillna(0)

    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(12,7))

    pivot.plot(
        kind="bar",
        stacked=True,
        ax=ax
    )

    ax.set_xlabel("Fonte")
    ax.set_ylabel("Número de artigos")
    ax.set_title("Distribuição dos Principais Temas por Fonte")

    plt.xticks(rotation=45)

    ax.legend(
        title="Focus",
        bbox_to_anchor=(1.05,1),
        loc="upper left"
    )

    plt.tight_layout()

    return fig

import pandas as pd
import matplotlib.pyplot as plt


def keyword_weight_chart(clusters_df):

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

    top_keywords = keyword_weight.head(20)

    fig, ax = plt.subplots(figsize=(10,7))

    top_keywords.sort_values().plot(
        kind="barh",
        ax=ax
    )

    ax.set_xlabel("Peso total (soma dos tamanhos dos clusters)")
    ax.set_ylabel("Palavra-chave")
    ax.set_title("Palavras-chave mais relevantes ponderadas pelo tamanho do cluster")

    plt.tight_layout()

    return fig

def keywords_wordcloud(clusters_df):

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
        background_color="white",
        colormap="Dark2"
    ).generate_from_frequencies(freq_dict)

    fig, ax = plt.subplots(figsize=(12,6))

    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Nuvem de Palavras das Keywords")

    return fig