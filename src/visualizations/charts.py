import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt


def cluster_distribution(df):

    if "cluster" not in df.columns:
        return None

    fig = px.histogram(
        df,
        x="cluster",
        title="Cluster Distribution"
    )

    return fig


def trend_frequency(df):

    if "trend" not in df.columns:
        return None

    counts = df["trend"].value_counts().head(20)

    fig = px.bar(
        x=counts.index,
        y=counts.values,
        title="Top Trends"
    )

    return fig