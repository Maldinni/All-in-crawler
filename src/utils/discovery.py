import re
from typing import List, Optional, Any, Dict, List
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
    headers = {"User-Agent": user_agent}
    r = requests.get(listing_url, headers=headers, timeout=timeout_sec)

    if r.status_code == 404:
        return []

    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    urls = []
    for a in soup.select(link_selector):
        href = (a.get("href") or "").strip()
        if not href:
            continue

        full = urljoin(listing_url, href)

        if allow_domains:
            netloc = urlparse(full).netloc
            if not any(netloc.endswith(d) for d in allow_domains):
                continue

        if "#" in full:
            continue

        if deny_url_patterns:
            if any(re.search(p, full) for p in deny_url_patterns):
                continue

        if allow_url_patterns:
            if not any(re.search(p, full) for p in allow_url_patterns):
                continue

        urls.append(full)

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
            pages.append(base.format(page=p))
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

def discover_urls_with_wp_pagination(source: Dict[str, Any], scraping: Dict[str, Any]) -> List[str]:
    start = int(source.get("pagination", {}).get("start", 1))
    max_pages = int(source.get("pagination", {}).get("end", 200))
    base_url = source["url"]

    all_urls: List[str] = []
    prev_page_urls: set[str] = set()

    headers = {"User-Agent": scraping["user_agent"]}
    timeout = int(scraping["timeout_sec"])

    for page in range(start, max_pages + 1):
        if "{page}" in base_url:
            page_url = base_url.format(page=page)
        else:
            if page == 1:
                page_url = base_url
            else:
                if not base_url.endswith("/"):
                    base_url_slash = base_url + "/"
                else:
                    base_url_slash = base_url
                page_url = base_url_slash + f"page/{page}/"

        try:
            r = requests.get(page_url, headers=headers, timeout=timeout)
            if r.status_code == 404:
                break
            r.raise_for_status()
        except requests.HTTPError as e:
            break
        except Exception:
            break

        page_urls = discover_article_urls_listing(
            listing_url=page_url,
            allow_domains=source.get("allow_domains"),
            user_agent=scraping["user_agent"],
            timeout_sec=timeout,
            link_selector=source.get("link_selector", "a[href]"),
            allow_url_patterns=source.get("allow_url_patterns"),
            deny_url_patterns=source.get("deny_url_patterns"),
        )

        if not page_urls:
            break

        page_set = set(page_urls)
        if page_set == prev_page_urls:
            break
        prev_page_urls = page_set

        all_urls.extend(page_urls)

    seen = set()
    out = []
    for u in all_urls:
        if u not in seen:
            out.append(u)
            seen.add(u)
    return out

def discover_g1_urls_follow_see_more(
    start_url: str,
    allow_domains,
    user_agent: str,
    timeout_sec: int,
    link_selector: str = "a.feed-post-link",
    allow_url_patterns=None,
    deny_url_patterns=None,
    max_pages: int = 30,
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

        see_more = soup.find("a", string=re.compile(r"Veja mais", re.I))
        if not see_more or not see_more.get("href"):
            break

        next_page = urljoin(next_page, see_more["href"])

    seen = set()
    out = []
    for u in all_urls:
        if u not in seen:
            out.append(u)
            seen.add(u)

    return out