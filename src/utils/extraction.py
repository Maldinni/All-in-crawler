from typing import Any, Dict, Optional
from time import sleep

from newspaper import Article


def extract_article_newspaper(url: str, language: str = "pt") -> Dict[str, Any]:
    a = Article(url, language=language)
    a.download()
    a.parse()

    # a.nlp() pode falhar se NLTK ou texto insuficiente
    try:
        a.nlp()
    except Exception:
        pass

    return {
        "url": url,
        "title": a.title or None,
        "authors": a.authors or [],
        "publish_date": a.publish_date.isoformat() if a.publish_date else None,
        "text": a.text or None,
        "top_image": a.top_image or None,
        "keywords": getattr(a, "keywords", None),
        "summary": getattr(a, "summary", None),
    }


def extract_with_retry(url: str, num_attempts: int, sleep_time: float) -> Optional[Dict[str, Any]]:
    last_err = None
    for _ in range(num_attempts):
        try:
            return extract_article_newspaper(url)
        except Exception as e:
            last_err = e
            sleep(sleep_time)
    return None
