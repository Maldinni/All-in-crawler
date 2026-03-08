import os
from anyio import Path
import pandas as pd
from glob import glob

from src.utils.parsing import parse_args, load_config, extract_cluster_id
from src.utils.io import ensure_dirs, load_and_parse_cluster_file

def main():

    args = parse_args()
    cfg = load_config(args)

    paths = cfg["paths"]
    ensure_dirs(paths["raw"], paths["processed"], paths["checkpoints"], paths["output"])

    clusters_directory = f'{cfg["paths"]["output"]}'
    output_directory = f'{cfg["paths"]["processed"]}'

    cluster_json_file = 'clusters_defined.json'
    cluster_csv_file = 'clusters_defined.csv'
    dataset_file = Path(cfg["paths"]["processed"]) / "articles_merged_cleaned_clustered.csv"

    files = glob(os.path.join(clusters_directory, "*.txt"))

    df = pd.read_csv(dataset_file)

    cluster_sizes = df.groupby("Cluster ID").size()

    cluster_records = []

    for file in files:

        cluster_id = extract_cluster_id(file)

        keywords, title, description, focus = load_and_parse_cluster_file(file)

        record = {
            "Cluster ID": cluster_id,
            "Title": title,
            "Size": int(cluster_sizes.get(cluster_id, 0)),
            "Keywords": "; ".join(keywords),
            "Description": description,
            "Focus": focus,
            "Most Similar Cluster": "",
            "Similarity": ""
        }

        cluster_records.append(record)

    clusters_df = pd.DataFrame(cluster_records)

    clusters_df = clusters_df.sort_values("Cluster ID")

    clusters_df.to_csv(os.path.join(output_directory, cluster_csv_file), index=False)

    clusters_df.to_json(
        os.path.join(output_directory, cluster_json_file),
        orient="records",
        indent=2,
        force_ascii=False
    )

    print("Dataset criado com sucesso!")


if __name__ == "__main__":
    main()