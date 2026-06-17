"""
google_news.py — coleta de notícias via Google News RSS.

O Google News expõe um feed RSS de busca aberto (sem API key) para qualquer
termo. Usamos isso para garantir a coleta de notícias sobre atores/clientes
monitorados, mesmo de veículos fora da lista de fontes em sources.toml.
"""

import re
import hashlib
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import requests

from src.utils.extraction import normalize_url, normalize_whitespace, limit_words


def _strip_html(text):
    return normalize_whitespace(re.sub(r"<[^>]+>", " ", text or ""))


def discover_google_news_items(
    query,
    lang="pt-BR",
    country="BR",
    user_agent="Mozilla/5.0",
    timeout_sec=20,
    max_items=100,
):
    """Busca no Google News RSS e devolve uma lista de itens (dicts)."""
    ceid = f"{country}:{lang.split('-')[0]}"
    url = (
        "https://news.google.com/rss/search?q="
        + quote(query)
        + f"&hl={lang}&gl={country}&ceid={quote(ceid)}"
    )

    headers = {"User-Agent": user_agent, "Accept-Language": f"{lang},pt;q=0.9"}
    resp = requests.get(url, headers=headers, timeout=timeout_sec)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    items = []

    for it in root.findall(".//item")[:max_items]:
        link = (it.findtext("link") or "").strip()
        if not link:
            continue

        title = (it.findtext("title") or "").strip()
        src_el = it.find("source")
        publisher = (src_el.text or "").strip() if src_el is not None else ""

        # o Google sufixa o título com " - <Veículo>"; remove se for o caso
        if publisher and title.endswith(f"- {publisher}"):
            title = title[: -len(f"- {publisher}")].strip()

        snippet = _strip_html(it.findtext("description") or "")

        pub_raw = it.findtext("pubDate")
        try:
            publish_date = parsedate_to_datetime(pub_raw).isoformat() if pub_raw else None
        except (TypeError, ValueError):
            publish_date = None

        items.append({
            "title": title,
            "url": link,
            "canonical_url": normalize_url(link),
            "publish_date": publish_date,
            "publisher": publisher,
            "snippet": snippet,
        })

    return items


def build_google_news_record(source_name, item):
    """Converte um item do RSS no mesmo schema dos artigos raspados."""
    title = item.get("title") or ""
    snippet = item.get("snippet") or ""
    text = f"{title}. {snippet}".strip() if snippet else title
    text = limit_words(text, 1000) or title

    word_count = len(text.split()) if text else 0

    return {
        "source": source_name,
        "domain": item.get("publisher") or "news.google.com",
        "canonical_url": item["canonical_url"],
        "url": item["url"],
        "title": title or None,
        "authors": [],
        "publish_date": item.get("publish_date"),
        "text": text,
        "word_count": word_count,
        "text_hash": hashlib.sha1(text.encode("utf-8")).hexdigest() if text else None,
    }
