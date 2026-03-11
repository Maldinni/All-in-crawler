import os
import re
import numpy as np
import pandas as pd
from pathlib import Path
from glob import glob

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

from src.utils.parsing import parse_args, load_config, extract_cluster_id, clean_llm_text
from src.utils.hypersphere import get_centroids
from src.utils.io import load_embedding_shards, align_to_df

def normalize_llm_output(text):

    # força quebra antes de cada dimensão
    text = re.sub(r'\s*(Dimensão\s*\d+)', r'\n\1', text)

    # remove espaços duplicados mas preserva quebra de linha
    text = re.sub(r'[ \t]+', ' ', text)

    # remove espaço antes da quebra de linha
    text = re.sub(r' \n', '\n', text)

    return text.strip()

def main():

    DIMENSIONS_PROMPT = PromptTemplate(
        input_variables=["title", "texts"],
        template="""
            Leia os textos abaixo e descreva as principais dimensões discursivas do cluster.

            Título do Cluster:
            {title}

            Textos:
            {texts}

            Identifique de forma concisa:

            Posicionamento Social e Político: apoio, crítica ou neutralidade em relação a temas sociais ou políticos.

            Tom Emocional: sentimento predominante (ex: neutro, crítico, alarmista, sensacionalista).

            Enquadramento do Problema: forma como o problema é apresentado (ex: foco em causas, consequências, responsabilização de atores).

            Centralidade de Atores Sociais: grupos ou atores mais mencionados (ex: governo, polícia, vítimas, políticos, população).

            Foco em Instituições ou Indivíduos: se o destaque está em organizações (ex: governo, polícia) ou em pessoas específicas.

            Alcance Geográfico: nível do tema (ex: local, regional, nacional, internacional).

            Evento Pontual ou Problema Estrutural: se o texto descreve um fato isolado ou um problema recorrente.

            Uso de Evidências e Fontes: presença de dados, estatísticas, especialistas ou declarações oficiais.

            Tipo de Veículo de Mídia: origem do conteúdo (ex: notícia jornalística, rede social, comunicado oficial).

            Saída:

            - Dimensão 1 - Posicionamento Social e Político:
            - Dimensão 2 - Tom Emocional:
            - Dimensão 3 - Enquadramento do Problema:
            - Dimensão 4 - Centralidade de Atores Sociais:
            - Dimensão 5 - Foco em Instituições ou Indivíduos:
            - Dimensão 6 - Alcance Geográfico:
            - Dimensão 7 - Evento Pontual ou Problema Estrutural:
            - Dimensão 8 - Uso de Evidências e Fontes:
            - Dimensão 9 - Tipo de Veículo de Mídia:
        """
    )

    args = parse_args()
    cfg = load_config(args)

    llm = ChatOllama(
        model=cfg["llm"]["model_name"],
        temperature=cfg["llm"]["temperature"]
    )

    dimensions_chain = DIMENSIONS_PROMPT | llm

    processed_path = Path(cfg["paths"]["processed"])
    output_path = Path(cfg["paths"]["output"])

    articles_file = processed_path / "articles_merged_cleaned_clustered.csv"
    clusters_file = processed_path / "clusters_defined_distinguished_trends.csv"

    output_dir = output_path / "assess_dimensions"

    os.makedirs(output_dir, exist_ok=True)

    article_df = pd.read_csv(articles_file)
    cluster_df = pd.read_csv(clusters_file)

    shard_directory = Path(cfg["paths"]["raw"]) / "shards_h5"
    files = glob(os.path.join(shard_directory, '*.h5'))


    embeddings, texts = load_embedding_shards(files)

    aligned_embeddings, aligned_texts = align_to_df(
        embeddings,
        texts,
        article_df
    )

    centroids = get_centroids(
        aligned_embeddings,
        article_df["Cluster ID"].values
    )

    labels = article_df["Cluster ID"].values
    texts = article_df["text"].values

    print("Iniciando análise de dimensões dos clusters...")

    for label, centroid in enumerate(centroids):

        output_file = output_dir / f"cluster_{label}_dimensions.txt"

        if output_file.exists():
            print(f"Cluster {label} já processado.")
            continue

        cluster_texts = texts[labels == label]
        cluster_embeddings = aligned_embeddings[labels == label]

        number_of_texts = min(
            cfg['dimensions']['max_article_number'],
            len(cluster_texts)
        )

        similarity = centroid.dot(cluster_embeddings.T)
        top_indices = np.argsort(similarity)[::-1][:number_of_texts]

        selected_texts = cluster_texts[top_indices]

        cluster_title = cluster_df.loc[label, "Title"]

        chain_input = {
            "title": cluster_title,
            "texts": "\n\n".join(selected_texts)
        }

        raw_output = dimensions_chain.invoke(chain_input)

        cleaned_output = clean_llm_text(raw_output.content)
        
        normalized_output = normalize_llm_output(cleaned_output)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(normalized_output)

        print(f"Cluster {label} salvo.")


def json_converter():

    args = parse_args()
    cfg = load_config(args)

    processed_path = Path(cfg["paths"]["processed"])
    output_path = Path(cfg["paths"]["output"])

    clusters_file = processed_path / "clusters_defined_distinguished_trends.csv"
    cluster_df = pd.read_csv(clusters_file)

    dimensions_dir = output_path / "assess_dimensions"

    files = glob(os.path.join(dimensions_dir, "*.txt"))

    dimensions = []

    for file in files:

        cluster_id = extract_cluster_id(file)

        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        dimensions.append({
            "Cluster ID": cluster_id,
            "Dimensions": text
        })

    dim_df = pd.DataFrame(dimensions)

    final_df = cluster_df.merge(
        dim_df,
        on="Cluster ID",
        how="left"
    )

    output_file = processed_path / \
        "clusters_defined_distinguished_trends_assessed.csv"

    final_df.to_csv(output_file, index=False)

    print("Dataset final criado.")


if __name__ == "__main__":
    main()
    json_converter()