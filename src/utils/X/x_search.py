# src/utils/X/x_search.py
import os
import time
import requests

from config.settings import X_BEARER_TOKEN

X_SEARCH_URL = "https://api.x.com/2/tweets/search/recent"  # ou https://api.twitter.com/2/tweets/search/recent

def search_recent_tweets(query: str, max_results: int = 50, pages: int = 2, bearer_token: str | None = None):
    bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
    if not bearer_token:
        raise RuntimeError("Missing X_BEARER_TOKEN env var (Bearer Token do X).")

    headers = {"Authorization": f"Bearer {bearer_token}"}
    params = {
        "query": query,
        "max_results": max(10, min(int(max_results), 100)),
        "tweet.fields": "id,text,created_at,author_id",
        "expansions": "author_id",
        "user.fields": "id,name,username",
    }

    next_token = None
    out: list[tuple[dict, dict]] = []

    for _ in range(max(1, int(pages))):
        if next_token:
            params["next_token"] = next_token
        else:
            params.pop("next_token", None)

        resp = requests.get(X_SEARCH_URL, headers=headers, params=params, timeout=30)

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("retry-after", "60"))
            time.sleep(retry_after)
            continue

        resp.raise_for_status()
        payload = resp.json()

        tweets = payload.get("data") or []
        users = (payload.get("includes") or {}).get("users") or []
        user_by_id = {u["id"]: u for u in users if "id" in u}

        for t in tweets:
            author = user_by_id.get(t.get("author_id"), {}) or {}
            out.append((t, author))

        meta = payload.get("meta") or {}
        next_token = meta.get("next_token")
        if not next_token:
            break

    return out
