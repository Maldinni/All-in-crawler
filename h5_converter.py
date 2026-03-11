import os
import glob
import pickle
from pathlib import Path
from src.utils.parsing import parse_args, load_config
from src.utils.io import ensure_dirs, save_news_to_hdf5

def main():
    args = parse_args()
    cfg = load_config(args)

    paths = cfg["paths"]
    ensure_dirs(paths["raw"], paths["processed"], paths["checkpoints"], paths["output"])

    embedded_directory = Path(cfg["paths"]["raw"]) / "embedded"
    shard_directory = Path(cfg["paths"]["raw"]) / "shards_h5"

    # Ensure embedding output directory exists
    os.makedirs(shard_directory, exist_ok=True)

    # Convert all pickle shards to HDF5 format
    for pkl_file in embedded_directory.glob("*.pkl"):

        print(f"Convertendo {pkl_file.name}...")

        # Carrega pickle
        with open(pkl_file, "rb") as f:
            obj = pickle.load(f)

        print(type(obj))
        print(obj.__dict__.keys())
        # Define nome do .h5
        h5_filename = shard_directory / (pkl_file.stem + ".h5")

        # Salva em HDF5
        news_list = []

        for i in range(len(obj.texts)):
            article = {
                "text": obj.texts[i],
                "embedding": obj.embeddings[i] if i < len(obj.embeddings) else None
            }
            news_list.append(article)

        save_news_to_hdf5(news_list, str(h5_filename))

    print("Conversão finalizada.")

if __name__ == '__main__':
    main()