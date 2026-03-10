import os
import pandas as pd
from pathlib import Path
from tqdm import tqdm

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

from src.utils.parsing import parse_args, load_config
from src.utils.io import ensure_dirs


def truncate(text, max_chars=2000):
    return text[:max_chars]


def main():

    TRENDS_PROMPT = PromptTemplate(
        input_variables=["title", "date", "old_news", "recent_news"],
        template="""
            Compare dois conjuntos de textos sobre o tema "{title}".

            Conjunto 1: textos antigos (antes de {date})
            Conjunto 2: textos recentes (depois de {date})

            Identifique diferenças entre os dois conjuntos.

            Procure por:
            - Narrativas que aparecem ou ganham destaque nos textos recentes
            - Atores que aparecem ou ganham destaque nos textos recentes
            - Narrativas que eram comuns nos textos antigos mas aparecem menos nos recentes
            - Atores que eram comuns nos textos antigos mas aparecem menos nos recentes

            Retorne o resultado em JSON:

            {
            "Narrativas Emergentes": "lista separada por ponto e vírgula com breves descrições",
            "Atores Emergentes": "lista separada por ponto e vírgula com breves descrições",
            "Narrativas em Declínio": "lista separada por ponto e vírgula com breves descrições",
            "Atores em Declínio": "lista separada por ponto e vírgula com breves descrições"
            }

            Use apenas informações presentes nos textos.

            Textos antigos:
            {old_news}

            Textos recentes:
            {recent_news}
""",
    )

    args = parse_args()
    cfg = load_config(args)

    paths = cfg["paths"]
    ensure_dirs(paths["raw"], paths["processed"], paths["checkpoints"], paths["output"])

    num_news_per_set = cfg['trends']['max_abstract_number'] // 2
    recent_cutoff = cfg['trends']['recent_cutoff']
    older_cutoff = cfg['trends']['older_cutoff']

    llm = ChatOllama(
        model=cfg["llm"]["model_name"],
        temperature=cfg["llm"]["temperature"]
    )

    trends_chain = TRENDS_PROMPT | llm

    processed_path = Path(cfg["paths"]["processed"])
    output_path = Path(cfg["paths"]["output"]) / "cluster_trends"

    os.makedirs(output_path, exist_ok=True)

    news_file = processed_path / "articles_merged_cleaned_clustered.csv"
    clusters_file = processed_path / "clusters_defined.csv"

    news_df = pd.read_csv(news_file)
    cluster_df = pd.read_csv(clusters_file)

    news_df["date"] = pd.to_datetime(news_df["date"])

    labels = news_df["Cluster ID"].unique()

    print("Iniciando processamento de clusters...")

    for label in tqdm(labels):

        print(f"Processando cluster {label}...")

        older_news_list = news_df[
            (news_df["Cluster ID"] == label) &
            (news_df["date"] >= older_cutoff) &
            (news_df["date"] < recent_cutoff)
        ]["texts"].dropna().values

        n_old = min(num_news_per_set, len(older_news_list))

        if n_old == 0:
            continue

        older_news = "\n\n".join(
            [truncate(t) for t in older_news_list[:n_old]]
        )

        recent_df = news_df[
            (news_df["Cluster ID"] == label) &
            (news_df["date"] >= recent_cutoff)
        ].sort_values("date", ascending=False)

        recent_news_list = recent_df["texts"].dropna().values[:num_news_per_set]

        if len(recent_news_list) == 0:
            continue

        recent_news = "\n\n".join(
            [truncate(t) for t in recent_news_list]
        )

        title_row = cluster_df[cluster_df["Cluster ID"] == label]

        if title_row.empty:
            cluster_title = f"Cluster {label}"
        else:
            cluster_title = title_row.iloc[0]["Title"]

        chain_input = {
            "title": cluster_title,
            "date": str(recent_cutoff),
            "old_news": older_news,
            "recent_news": recent_news
        }

        raw_output = trends_chain.invoke(chain_input)

        with open(output_path / f"cluster_{label}.txt", "w", encoding="utf-8") as f:
            f.write(raw_output.content)

        print(f"Cluster {label} salvo.")


if __name__ == '__main__':
    main()