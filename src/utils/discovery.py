import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def discover_article_urls_listing(
    listing_url: str,
    allow_domains: Optional[List[str]],
    user_agent: str,
    timeout_sec: int,
) -> List[str]:
    headers = {"User-Agent": user_agent}
    r = requests.get(listing_url, headers=headers, timeout=timeout_sec)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    urls = []
    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        full = urljoin(listing_url, href)

        # filtra domínios
        if allow_domains:
            netloc = urlparse(full).netloc
            if not any(netloc.endswith(d) for d in allow_domains):
                continue

        # heurística: ignora âncoras e coisas óbvias que não são notícia
        if "#" in full:
            continue
        urls.append(full)

    # dedup preservando ordem
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            out.append(u)
            seen.add(u)
    return out
