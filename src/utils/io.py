import csv
import h5py
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from tqdm import tqdm

CSV_FIELDS = [
    "source",
    "domain",
    "canonical_url",
    "title",
    "authors",
    "publish_date",
    "text"
]

def ensure_dirs(*paths: str) -> None:
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)

def determine_output_filename(output_dir: str, ext: str = "csv") -> Tuple[str, int]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    existing = sorted(out.glob(f"shard_*.{ext}"))
    if not existing:
        return str(out / f"shard_{0:04d}.{ext}"), 0

    last = existing[-1].stem
    shard_id = int(last.split("_")[1]) + 1
    return str(out / f"shard_{shard_id:04d}.{ext}"), shard_id


def append_csv(path: str, records: List[Dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    file_exists = p.exists()

    with p.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)

        if not file_exists:
            writer.writeheader()

        for r in records:
            row = {}
            for k in CSV_FIELDS:
                v = r.get(k)

                if isinstance(v, list):
                    v = "; ".join(str(x) for x in v)

                row[k] = v

            writer.writerow(row)

def save_news_to_hdf5(news_list, filename, disable_tqdm=False):
    """
    Save news dataset to HDF5.

    Parameters:
    - news_list: list of dicts or objects with attributes
    - filename: str
    """

    with h5py.File(filename, 'w') as file:

        n = len(news_list)

        # String datasets
        sources = file.create_dataset('source', (n,),
                                       dtype=h5py.string_dtype())
        domains = file.create_dataset('domain', (n,),
                                       dtype=h5py.string_dtype())
        urls = file.create_dataset('canonical_url', (n,),
                                    dtype=h5py.string_dtype())
        titles = file.create_dataset('title', (n,),
                                      dtype=h5py.string_dtype())
        authors = file.create_dataset('authors', (n,),
                                       dtype=h5py.string_dtype())
        publish_dates = file.create_dataset('publish_date', (n,),
                                             dtype=h5py.string_dtype())
        texts = file.create_dataset('text', (n,),
                                      dtype=h5py.string_dtype())

        # Optional embedding group (if you generate later)
        embedding_group = file.create_group('embeddings')

        for i, article in tqdm(enumerate(news_list),
                               total=n,
                               disable=disable_tqdm):

            sources[i] = article["source"]
            domains[i] = article["domain"]
            urls[i] = article["canonical_url"]
            titles[i] = article["title"]
            authors[i] = article["authors"] if article["authors"] else ""
            publish_dates[i] = article["publish_date"]
            texts[i] = article["text"]

            # Se tiver embedding
            if "embedding" in article and article["embedding"] is not None:
                embedding_group.create_dataset(
                    str(i),
                    data=np.array(article["embedding"], dtype=np.float32),
                    dtype='f'
                )
            else:
                embedding_group.create_dataset(str(i), shape=(0,), dtype='f')