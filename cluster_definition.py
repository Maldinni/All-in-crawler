import os
import numpy as np
import pandas as pd
import sys
from glob import glob
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers.json import SimpleJsonOutputParser

from src.utils.parsing import parse_args, load_config
from src.utils.hypersphere import get_centroids
from src.utils.io import ensure_dirs, load_embedding_shards, align_to_df
from src.utils.semantic import safe_dictionary_extraction, get_article_strings

def main():

# Define prompt templates
    DEFINITION_PROMPT = PromptTemplate(
        input_variables=["articles"],
        template="""
                Você receberá um conjunto de textos jornalísticos pertencentes a um mesmo cluster temático.

                Todos os textos tratam de um mesmo fenômeno social, político ou institucional.

                Sua tarefa é analisar exclusivamente o conteúdo fornecido e produzir uma síntese estruturada seguindo exatamente o formato abaixo.

                Regras fundamentais:

                - Utilize apenas informações que estejam explicitamente presentes nos textos.
                - Não faça inferências externas.
                - Não adicione contexto histórico ou político que não esteja nos textos.
                - Não generalize além do que é dito.
                - Seja preciso e objetivo.
                - Não utilize comentários, explicações adicionais ou introduções.
                - Siga exatamente a estrutura solicitada.

                Estrutura obrigatória da resposta:

                Palavras-chave:
                - termo 1
                - termo 2
                - termo 3
                - termo 4
                - termo 5

                Título:
                Uma frase curta e descritiva que sintetize o fenômeno central abordado.

                Descrição:
                Escreva 1 ou 2 frases explicando:
                - qual é o fenômeno principal,
                - quem são os atores centrais,
                - qual é o contexto geral da cobertura.

                Foco:
                Escolha apenas uma das opções abaixo:
                Fenômeno Social
                Dinâmica Política/Institucional


                Critérios para definir o foco:

                - Escolha "Fenômeno Social" quando o centro da cobertura for um problema social, evento coletivo, comportamento social ou impacto na sociedade.
                - Escolha "Dinâmica Política/Institucional" quando o centro for disputas de poder, decisões governamentais, articulações políticas ou funcionamento de instituições.


                Textos para análise:

                {articles}
                """,
    )

    args = parse_args()
    cfg = load_config(args)

    paths = cfg["paths"]
    ensure_dirs(paths["raw"], paths["processed"], paths["checkpoints"], paths["output"])

    required_fields = cfg['definition']['required_fields']

    llm = ChatOllama(
        model="qwen3.5:27b",
        temperature=cfg['llm']['temperature']
    )

    csv_directory = f'{cfg["paths"]["processed"]}'
    csv_file = 'articles_merged_cleaned_clustered.csv'
    news_df = pd.read_csv(os.path.join(csv_directory, csv_file))
    output_directory = f'{cfg["paths"]["output"]}'

    cluster_csv_file = 'clusters_defined.csv'
    output_path = os.path.join(output_directory, cluster_csv_file)

    if os.path.exists(output_path):
        cluster_definitions_df = pd.read_csv(output_path)
        cluster_definitions = cluster_definitions_df.to_dict('records')
        processed_clusters = set(cluster_definitions_df['Cluster ID'].values.tolist())
    else:
        cluster_definitions = []
        processed_clusters = set()
    
    shard_directory = Path(cfg["paths"]["raw"]) / "shards_h5"
    files = glob(os.path.join(shard_directory, '*.h5'))
    embeddings, urls = load_embedding_shards(files)

    aligned_embeddings, aligned_urls = align_to_df(embeddings, urls, news_df)

    # Free memory
    del embeddings
    del urls

    # Get the centroids of the clusters
    centroids = get_centroids(aligned_embeddings, news_df['Cluster ID'].values)
    centroid_similarities = centroids.dot(centroids.T) - np.eye(centroids.shape[0])

    # Get cluster labels
    labels = news_df['Cluster ID'].values

    # Get the abstracts
    texts = news_df['text'].values

    # Get the publication years of the articles
    years = news_df['publish_date'].values

    # Get the type of the articles
    #sources = news_df['source'].values
    definition_chain = DEFINITION_PROMPT | llm

    print("Iniciando processamento de clusters...")

    for label, centroid in enumerate(centroids):

        if label in processed_clusters:
            continue

        print(f"Processando cluster {label}...")

        cluster_embeddings = aligned_embeddings[labels == label]
        cluster_articles = texts[labels == label]

        number_of_articles = min(
            cfg['definition']['max_article_number'],
            len(cluster_articles)
        )

        cluster_articles = get_article_strings(
            centroid,
            cluster_embeddings,
            cluster_articles,
            number_of_articles
        )

        chain_input = {"articles": cluster_articles}

        raw_output = definition_chain.invoke(chain_input)

        with open(f"{output_directory}/cluster_{label}.txt", "w", encoding="utf-8") as f:
            f.write(raw_output.content)

        print(f"Cluster {label} salvo como texto bruto.")

if __name__ == '__main__':
    main()