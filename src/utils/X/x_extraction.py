# src/utils/X/x_extraction.py
#
# --- Scraping do X (Twitter) DESATIVADO por enquanto ---
# Todo o código abaixo foi comentado intencionalmente. Para reativar,
# descomente este arquivo, x_search.py, config/settings.py e o bloco
# correspondente em scraper.py.
#
# def normalize_x_record(source_name: str, tweet: dict, author: dict) -> dict:
#     text = (tweet.get("text") or "").replace("\n", " ").strip()
#     tweet_id = tweet.get("id") or ""
#     created_at = tweet.get("created_at") or ""
#
#     username = author.get("username") or ""
#     author_name = author.get("name") or ""
#
#     canonical_url = ""
#     if username and tweet_id:
#         canonical_url = f"https://x.com/{username}/status/{tweet_id}"
#     else:
#         canonical_url = f"x://status/{tweet_id}" if tweet_id else ""
#
#     authors = ""
#     if author_name and username:
#         authors = f"{author_name} (@{username})"
#     elif username:
#         authors = f"@{username}"
#     elif author_name:
#         authors = author_name
#
#     title = text[:80].strip() + ("…" if len(text) > 80 else "")
#     text_preview = text[:200].strip() + ("…" if len(text) > 200 else "")
#
#     return {
#         "source": source_name,
#         "publish_date": created_at,
#         "title": title,
#         "text_preview": text_preview,
#         "authors": authors,
#         "domain": "x.com",
#         "canonical_url": canonical_url,
#         # se você quiser manter o texto completo pro seu pipeline:
#         "text": text,
#         "id": tweet_id,
#     }
