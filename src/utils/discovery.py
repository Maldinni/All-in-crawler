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
    link_selector: str = "a[href]",
    allow_url_patterns: Optional[List[str]] = None,
    deny_url_patterns: Optional[List[str]] = None,
) -> List[str]:
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }

    r = requests.get(listing_url, headers=headers, timeout=timeout_sec)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    urls = []

    for a in soup.select(link_selector):
        href = a.get("href", "").strip()
        if not href:
            continue

        full = urljoin(listing_url, href)

        host = urlparse(full).netloc.lower()
        if any(bad in host for bad in ["whatsapp.com", "wa.me", "twitter.com", "t.me", "facebook.com", "instagram.com", "spotify.com"]):
            continue

        # filtra domínios
        if allow_domains:
            netloc = urlparse(full).netloc
            if not any(netloc.endswith(d) for d in allow_domains):
                continue

        # allow patterns (ex: /noticia/)
        if allow_url_patterns:
            if not any(re.search(p, full) for p in allow_url_patterns):
                continue

        # deny patterns (ex: /tag/, /videos/)
        if deny_url_patterns:
            if any(re.search(p, full) for p in deny_url_patterns):
                continue

        # ignora âncoras
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
