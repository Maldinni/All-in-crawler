import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def ensure_dirs(*paths: str) -> None:
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)


def determine_output_filename(output_dir: str, ext: str = "jsonl") -> Tuple[str, int]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    existing = sorted(out.glob(f"shard_*.{ext}"))
    if not existing:
        return str(out / f"shard_{0:04d}.{ext}"), 0
    last = existing[-1].stem  # shard_0007
    shard_id = int(last.split("_")[1]) + 1
    return str(out / f"shard_{shard_id:04d}.{ext}"), shard_id


def append_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
