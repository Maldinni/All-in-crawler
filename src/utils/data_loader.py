import pandas as pd


def load_results(path="data/clusters_defined_distinguished_trends_assessed.csv"):
    return pd.read_csv(path)


def search_dataframe(df, keyword):
    if not keyword:
        return df

    keyword = keyword.lower()

    mask = df.apply(
        lambda row: row.astype(str).str.lower().str.contains(keyword).any(),
        axis=1
    )

    return df[mask]