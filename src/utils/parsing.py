import argparse
import tomllib
from pathlib import Path
from typing import Any, Dict


def load_toml(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    raw = p.read_bytes()
    with open(p, "rb") as f:
        return tomllib.load(f)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="News scraping prototype")

    p.add_argument("--sources", default="config/ingestion/sources.toml")
    p.add_argument("--directories", default="config/directories.toml")
    p.add_argument("--scraping", default="config/ingestion/scraping.toml")
    p.add_argument("--cleaning", default="config/ingestion/cleaning.toml")

    p.add_argument("--source", default=None, help="Rodar apenas uma fonte por nome.")
    p.add_argument("--max_articles_per_source", type=int, default=None)
    p.add_argument("--dry_run", action="store_true")

    return p.parse_args()


def load_config(args: argparse.Namespace) -> Dict[str, Any]:
    dirs_file = load_toml(args.directories)
    scraping_file = load_toml(args.scraping)
    sources_file = load_toml(args.sources)
    cleaning_file = load_toml(args.cleaning)

    cfg = {
        "paths": dirs_file["paths"],
        "scraping": scraping_file["scraping"],
        "sharding": scraping_file.get("sharding", {}),
        "sources": sources_file["sources"],
        "runtime": {"source_filter": args.source, "dry_run": args.dry_run},
        "cutoff": cleaning_file["cutoff"],
        "word_limit": cleaning_file["word_limit"],
    }

    if args.max_articles_per_source is not None:
        cfg["scraping"]["max_articles_per_source"] = args.max_articles_per_source

    return cfg
