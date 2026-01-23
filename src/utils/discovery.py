import re
from typing import List, Optional
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse, urljoin

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

def build_listing_pages(source: dict) -> list[str]:
    base = source["url"]
    pag = source.get("pagination")
    if not pag:
        return [base]

    start = int(pag.get("start", 1))
    end = int(pag.get("end", start))
    mode = pag.get("mode")

    pages = []

    if mode == "path_format":
        for p in range(start, end + 1):
            pages.append(base.format(page=p))  # 🔑 substitui {page}
        return pages

    if mode == "query":
        page_param = pag.get("page_param", "page")
        u = urlparse(base)
        qs = parse_qs(u.query)

        for p in range(start, end + 1):
            qs[page_param] = [str(p)]
            new_query = urlencode(qs, doseq=True)
            pages.append(urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment)))

        return pages

    return [base]

def discover_g1_urls_follow_see_more(
    start_url: str,
    allow_domains,
    user_agent: str,
    timeout_sec: int,
    link_selector: str = "a.feed-post-link",
    allow_url_patterns=None,
    deny_url_patterns=None,
    max_pages: int = 30,   # segurança
):
    headers = {"User-Agent": user_agent}
    all_urls = []
    seen_pages = set()

    next_page = start_url

    for _ in range(max_pages):
        if next_page in seen_pages:
            break
        seen_pages.add(next_page)

        r = requests.get(next_page, headers=headers, timeout=timeout_sec)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # reaproveita sua lógica: pega links de matérias
        for a in soup.select(link_selector):
            href = (a.get("href") or "").strip()
            if not href:
                continue

            full = urljoin(next_page, href)

            if allow_domains:
                netloc = urlparse(full).netloc
                if not any(netloc.endswith(d) for d in allow_domains):
                    continue

            if allow_url_patterns:
                if not any(re.search(p, full) for p in allow_url_patterns):
                    continue

            if deny_url_patterns:
                if any(re.search(p, full) for p in deny_url_patterns):
                    continue

            if "#" in full:
                continue

            all_urls.append(full)

        # acha o próximo "Veja mais"
        see_more = soup.find("a", string=re.compile(r"Veja mais", re.I))
        if not see_more or not see_more.get("href"):
            break

        next_page = urljoin(next_page, see_more["href"])

    # dedup preservando ordem
    seen = set()
    out = []
    for u in all_urls:
        if u not in seen:
            out.append(u)
            seen.add(u)

    return out