import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple


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

    last = existing[-1].stem  # shard_0007
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
