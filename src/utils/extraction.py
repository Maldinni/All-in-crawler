import re
import requests
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse

from typing import Any, Dict, Optional
from time import sleep
from newspaper import Article

def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def limit_words(text: Optional[str], max_words: int = 1000) -> Optional[str]:
    if not text:
        return None
    text = normalize_whitespace(text)

    words = text.split(" ")
    if len(words) <= max_words:
        return text

    return " ".join(words[:max_words])


def normalize_url(url: str) -> str:
    """
    Remove tracking params e fragmentos para criar um canonical URL.
    """
    parts = urlparse(url)
    return urlunparse((parts.scheme, parts.netloc, parts.path, "", "", ""))


def extract_text_from_html(url: str, user_agent: str, timeout: int = 20) -> str:
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
        "Cache-Control": "no-cache",
    }

    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    paragraphs = []
    for p in soup.find_all("p"):
        txt = p.get_text(" ", strip=True)
        if len(txt) > 30:
            paragraphs.append(txt)

    text = " ".join(paragraphs)
    return normalize_whitespace(text)

def extract_article(
    url: str,
    source_name: str,
    user_agent: str,
    language: str = "pt"
) -> Dict[str, Any]:

    a = Article(url, language=language)
    a.download()
    a.parse()

    raw_text = a.text or ""
    raw_text = normalize_whitespace(raw_text)

    word_count = len(raw_text.split()) if raw_text else 0

    # Fallback se o newspaper falhar
    if word_count < 120:
        try:
            html_text = extract_text_from_html(url, user_agent)
            if len(html_text.split()) > word_count:
                raw_text = html_text
                word_count = len(raw_text.split())
        except Exception:
            pass

    canonical = normalize_url(url)
    text = limit_words(raw_text, 1000)

    return {
        "source": source_name,
        "domain": urlparse(url).netloc,
        "canonical_url": canonical,
        "url": url,
        "title": a.title or None,
        "authors": a.authors or [],
        "publish_date": a.publish_date.isoformat() if a.publish_date else None,
        "text": text,
        "word_count": word_count,
        "text_hash": hashlib.sha1(raw_text.encode("utf-8")).hexdigest() if raw_text else None,
    }

def extract_with_retry(
    url: str,
    source_name: str,
    user_agent: str,
    num_attempts: int,
    sleep_time: float
) -> Optional[Dict[str, Any]]:

    for _ in range(num_attempts):
        try:
            return extract_article(url, source_name, user_agent)
        except Exception:
            sleep(sleep_time)

    return None
