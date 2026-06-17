import argparse
import re
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
    p.add_argument("--clustering", default="config/clustering.toml")
    p.add_argument("--scraping", default="config/ingestion/scraping.toml")
    p.add_argument("--cleaning", default="config/ingestion/cleaning.toml")
    p.add_argument("--initial_embedding", default="config/ingestion/initial_embedding.toml")
    p.add_argument("--semantic", default="config/analysis/semantic.toml")

    p.add_argument("--source", default=None, help="Rodar apenas uma fonte por nome.")
    p.add_argument("--max_articles_per_source", type=int, default=None)
    p.add_argument("--dry_run", action="store_true")

    return p.parse_args()


def load_config(args: argparse.Namespace) -> Dict[str, Any]:
    dirs_file = load_toml(args.directories)
    scraping_file = load_toml(args.scraping)
    sources_file = load_toml(args.sources)
    cleaning_file = load_toml(args.cleaning)
    initial_embedding_file = load_toml(args.initial_embedding)
    graph_construction_file = load_toml(args.clustering)
    cluster_definition_file = load_toml(args.semantic)
    trends_file = load_toml(args.semantic)
    dimensions_file = load_toml(args.semantic)


    cfg = {
        "paths": dirs_file["paths"],
        "scraping": scraping_file["scraping"],
        "sharding": scraping_file.get("sharding", {}),
        "sources": sources_file["sources"],
        "runtime": {"source_filter": args.source, "dry_run": args.dry_run},
        "cutoff": cleaning_file["cutoff"],
        "word_limit": cleaning_file["word_limit"],
        "initial_embedding": initial_embedding_file,
        "graph_construction": graph_construction_file["graph_construction"],
        "community_detection": graph_construction_file["community_detection"],
        "definition": cluster_definition_file["definition"],
        "llm": cluster_definition_file["llm"],
        "trends": trends_file["trends"],
        "dimensions": dimensions_file["dimensions"]
    }

    if args.max_articles_per_source is not None:
        cfg["scraping"]["max_articles_per_source"] = args.max_articles_per_source

    return cfg

def extract_cluster_id(filename):
    # usa só o nome do arquivo (evita pegar dígitos do caminho) e ancora
    # no prefixo "cluster_" quando presente
    name = Path(filename).name
    match = re.search(r"cluster[_-]?(\d+)", name, re.I)
    if match is None:
        match = re.search(r"(\d+)", name)
    return int(match.group(1))


def _strip_markdown(text):
    """Remove marcação markdown (negrito, títulos, citações, crases)."""
    return re.sub(r"[*#`>]+", "", text)


def _clean_bullet(line):
    """Remove marcadores de lista (-, *, •, ·) e numeração (1. / 1))."""
    line = re.sub(r"^[\-\*•·–—]+\s*", "", line.strip())
    line = re.sub(r"^\d+[\.\)]\s*", "", line)
    return line.strip()


def load_and_parse_cluster_file(filepath):
    """Faz o parsing tolerante da saída do LLM (aceita markdown, variações
    de acento/maiúsculas e dois-pontos opcionais)."""

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    text = _strip_markdown(text)

    # keywords: bloco entre "Palavras-chave" e "Título"
    keywords = []
    kw_section = re.search(
        r"Palavras?\s*-?\s*chave\s*:?(.*?)(?=T[íi]tulo\s*:?)",
        text, re.S | re.I,
    )
    if kw_section:
        for line in kw_section.group(1).splitlines():
            item = _clean_bullet(line)
            if item:
                keywords.append(item)

    # título: primeira linha não-vazia após "Título"
    title = ""
    title_match = re.search(r"T[íi]tulo\s*:?\s*(.+)", text, re.I)
    if title_match:
        title = title_match.group(1).splitlines()[0].strip()

    # descrição: bloco entre "Descrição" e "Foco"
    description = ""
    desc_match = re.search(
        r"Descri[çc][ãa]o\s*:?(.*?)(?=Foco\s*:?)",
        text, re.S | re.I,
    )
    if desc_match:
        description = " ".join(desc_match.group(1).split()).strip()

    # foco: primeira linha não-vazia após "Foco"
    focus = ""
    focus_match = re.search(r"Foco\s*:?\s*(.+)", text, re.I)
    if focus_match:
        focus = focus_match.group(1).splitlines()[0].strip()

    return keywords, title, description, focus


def parse_distinction_file(filepath):
    """Extrai as diferenças do arquivo, tolerante a vários tipos de marcador."""

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    text = _strip_markdown(text)
    # remove o cabeçalho "Diferenças:" se existir
    text = re.sub(r"Diferen[çc]as\s*:?", "", text, flags=re.I)

    items = []
    for line in text.splitlines():
        item = _clean_bullet(line)
        if item:
            items.append(item)

    return "; ".join(items)


def clean_llm_text(text):

    text = re.sub(r"#+", "", text)      
    text = re.sub(r"\*\*", "", text)    
    text = re.sub(r"- ", "", text)       
    text = text.replace("\n", " ")       
    text = re.sub(r"\s+", " ", text)     

    return text.strip()