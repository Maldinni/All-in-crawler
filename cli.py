import os
import csv
import time
import tomllib
import requests
from urllib.parse import urlparse

from config.settings import X_BEARER_TOKEN

X_SEARCH_URL = "https://api.x.com/2/tweets/search/recent"  # às vezes também funciona com https://api.twitter.com/2/...

def load_sources(toml_path: str) -> dict:
    with open(toml_path, "rb") as f:
        data = tomllib.load(f)
    return data.get("sources", {})

def x_search_recent(query: str, bearer_token: str, max_results: int = 50, pages: int = 2):
    """
    Retorna uma lista de tweets (com includes.users) usando paginação por next_token.
    pages = quantas páginas você quer puxar (rate limit depende do seu plano).
    """
    headers = {"Authorization": f"Bearer {bearer_token}"}

    params = {
        "query": query,
        "max_results": max(10, min(int(max_results), 100)),
        "tweet.fields": "id,text,created_at,author_id",
        "expansions": "author_id",
        "user.fields": "id,name,username",
    }

    all_rows = []
    next_token = None

    for _ in range(max(1, pages)):
        if next_token:
            params["next_token"] = next_token
        else:
            params.pop("next_token", None)

        resp = requests.get(X_SEARCH_URL, headers=headers, params=params, timeout=30)

        # Rate limit / backoff simples
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("retry-after", "60"))
            time.sleep(retry_after)
            continue

        resp.raise_for_status()
        payload = resp.json()

        tweets = payload.get("data", []) or []
        includes = payload.get("includes", {}) or {}
        users = includes.get("users", []) or []
        user_by_id = {u["id"]: u for u in users if "id" in u}

        for t in tweets:
            author = user_by_id.get(t.get("author_id"), {})
            all_rows.append((t, author))

        meta = payload.get("meta", {}) or {}
        next_token = meta.get("next_token")
        if not next_token:
            break

    return all_rows

def to_output_row(source_name: str, tweet: dict, author: dict):
    text = (tweet.get("text") or "").replace("\n", " ").strip()
    username = author.get("username") or ""
    tweet_id = tweet.get("id") or ""

    canonical_url = ""
    if username and tweet_id:
        canonical_url = f"https://x.com/{username}/status/{tweet_id}"

    # domain: pro X puro, o domínio será x.com
    domain = urlparse(canonical_url).netloc or "x.com"

    # “title”: tweet não tem título; dá pra usar uma versão curta do texto
    title = text[:80].strip()
    if len(text) > 80:
        title += "…"

    text_preview = text[:200].strip()
    if len(text) > 200:
        text_preview += "…"

    # authors: pode ser "Name (@username)" ou só @username
    author_name = author.get("name") or ""
    authors = ""
    if author_name and username:
        authors = f"{author_name} (@{username})"
    elif username:
        authors = f"@{username}"
    elif author_name:
        authors = author_name

    publish_date = tweet.get("created_at") or ""

    return {
        "source": source_name,
        "publish_date": publish_date,
        "title": title,
        "text_preview": text_preview,
        "authors": authors,
        "domain": domain,
        "canonical_url": canonical_url,
    }

def run(toml_path: str, out_csv: str, pages_per_source: int = 2):
    bearer = X_BEARER_TOKEN
    if not bearer:
        raise RuntimeError("Defina a env var X_BEARER_TOKEN com seu Bearer Token.")

    sources = load_sources(toml_path)
    if not sources:
        raise RuntimeError("Nenhum [sources] encontrado no TOML.")

    fieldnames = ["source","publish_date","title","text_preview","authors","domain","canonical_url"]

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for source_name, cfg in sources.items():
            query = cfg["query"]
            max_results = int(cfg.get("max_results", 50))

            pairs = x_search_recent(
                query=query,
                bearer_token=bearer,
                max_results=max_results,
                pages=pages_per_source,
            )

            for tweet, author in pairs:
                row = to_output_row(source_name, tweet, author)
                w.writerow(row)

if __name__ == "__main__":
    run("config/ingestion/sources.toml", "x_results.csv", pages_per_source=2)
