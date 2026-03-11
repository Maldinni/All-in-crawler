import os
import glob
import pickle
import pandas as pd
from pathlib import Path
from src.utils.organizing import ordenate_clusters, split_clusters
from src.utils.parsing import parse_args, load_config
from src.utils.io import ensure_dirs, save_organized_clusters

def main():
    args = parse_args()
    cfg = load_config(args)

    paths = cfg["paths"]
    ensure_dirs(paths["raw"], paths["processed"], paths["checkpoints"], paths["output"])

    cluster_input_directory = Path(cfg["paths"]["processed"])

    cluster_output_directory = Path(cfg["paths"]["processed"]) / "separated clusters"

    cluster_file = os.path.join(cluster_input_directory, 'articles_merged_cleaned_clustered.csv')

    df = pd.read_csv(cluster_file)

    df = ordenate_clusters(df)

    save_organized_clusters(df, cluster_input_directory)

    split_clusters(df, cluster_output_directory)

    print("Organização finalizada.")

if __name__ == '__main__':
    main()