from time import sleep

from src.utils.parsing import parse_args, load_config
from src.utils.checkpoints import load_processed_urls, save_processed_urls
from src.utils.discovery import (
    discover_article_urls_listing,
    build_listing_pages,
    discover_g1_urls_follow_see_more,
    discover_urls_with_wp_pagination,
)
from src.utils.extraction import extract_with_retry
from src.utils.google_news import discover_google_news_items, build_google_news_record
from src.utils.io import ensure_dirs, determine_output_filename, append_csv

# --- Scraping do X (Twitter) desativado por enquanto ---
# from src.utils.X.x_search import search_recent_tweets
# from src.utils.X.x_extraction import normalize_x_record


def main():
    args = parse_args()
    cfg = load_config(args)

    paths = cfg["paths"]
    scraping = cfg["scraping"]
    sources = cfg["sources"]
    runtime = cfg["runtime"]
    sharding = cfg["sharding"]

    ensure_dirs(paths["raw"], paths["processed"], paths["checkpoints"], paths["output"])

    processed_path = f'{paths["checkpoints"]}/processed_urls.json'
    processed = load_processed_urls(processed_path)

    output_file, shard_id = determine_output_filename(
        paths["raw"], ext=sharding.get("format", "jsonl")
    )
    buffer = []
    items_per_shard = int(sharding.get("items_per_shard", 200))

    if runtime["source_filter"]:
        sources = [s for s in sources if s["name"] == runtime["source_filter"]]

    for source in sources:
        print(f'\n=== Source: {source["name"]} ({source["type"]}) ===')

        if source["type"] == "listing":
            try:
                all_urls: list[str] = []

                # 1) Caso especial G1 (segue o "Veja mais")
                if source["name"] in ("G1", "G1 Piauí"):
                    urls = discover_g1_urls_follow_see_more(
                        start_url=source["url"],
                        allow_domains=source.get("allow_domains"),
                        user_agent=scraping["user_agent"],
                        timeout_sec=int(scraping["timeout_sec"]),
                        link_selector=source.get("link_selector", "a[href]"),
                        allow_url_patterns=source.get("allow_url_patterns"),
                        deny_url_patterns=source.get("deny_url_patterns"),
                        max_pages=int(scraping.get("max_pages_per_source", 100)),
                    )
                    all_urls.extend(urls)

                # 2) WordPress pagination (/page/2/, /page/3/...) com "stop on 404/empty"
                elif source["name"].startswith("Boletim Brio"):
                    urls = discover_urls_with_wp_pagination(source, scraping)
                    all_urls.extend(urls)

                # 3) Padrão: paginação configurada no TOML (build_listing_pages)
                else:
                    listing_pages = build_listing_pages(source)
                    for listing_url in listing_pages:
                        urls = discover_article_urls_listing(
                            listing_url=listing_url,
                            allow_domains=source.get("allow_domains"),
                            user_agent=scraping["user_agent"],
                            timeout_sec=int(scraping["timeout_sec"]),
                            link_selector=source.get("link_selector", "a[href]"),
                            allow_url_patterns=source.get("allow_url_patterns"),
                            deny_url_patterns=source.get("deny_url_patterns"),
                        )
                        all_urls.extend(urls)

            except Exception as e:
                print(f"[WARN] Failed to discover URLs for {source['name']}: {e}")
                continue

            # dedup preservando ordem
            seen = set()
            urls = []
            for u in all_urls:
                if u not in seen:
                    urls.append(u)
                    seen.add(u)

            # limite
            urls = urls[: int(scraping["max_articles_per_source"])]
            print(f"Discovered URLs: {len(urls)} (limit applied)")

            for url in urls:
                if url in processed:
                    continue

                if runtime["dry_run"]:
                    print("[dry-run]", url)
                    processed.add(url)
                    continue

                data = extract_with_retry(
                    url,
                    source["name"],
                    scraping["user_agent"],
                    int(scraping["num_attempts"]),
                    float(scraping["sleep_time"]),
                )

                if not data or not data.get("text"):
                    continue

                data["source"] = source["name"]
                buffer.append(data)
                processed.add(url)

                if len(buffer) >= items_per_shard:
                    append_csv(output_file, buffer)
                    save_processed_urls(processed_path, processed)
                    buffer = []
                    output_file, shard_id = determine_output_filename(
                        paths["raw"], ext=sharding.get("format", "jsonl")
                    )
                    print(f"Flushed shard -> {output_file}")

                sleep(float(scraping["sleep_time"]))

            save_processed_urls(processed_path, processed)
            continue  # importante: não cair no fluxo de outros types

        if source["type"] == "google_news":
            try:
                items = discover_google_news_items(
                    query=source["query"],
                    lang=source.get("lang", "pt-BR"),
                    country=source.get("country", "BR"),
                    user_agent=scraping["user_agent"],
                    timeout_sec=int(scraping["timeout_sec"]),
                    max_items=int(scraping["max_articles_per_source"]),
                )
            except Exception as e:
                print(f"[WARN] Falha no Google News para {source['name']}: {e}")
                continue

            print(f"Discovered news items: {len(items)}")

            for item in items:
                key = item["canonical_url"]
                if not key or key in processed:
                    continue

                if runtime["dry_run"]:
                    print("[dry-run]", key)
                    processed.add(key)
                    continue

                record = build_google_news_record(source["name"], item)
                record["source"] = source["name"]
                buffer.append(record)
                processed.add(key)

                if len(buffer) >= items_per_shard:
                    append_csv(output_file, buffer)
                    save_processed_urls(processed_path, processed)
                    buffer = []
                    output_file, shard_id = determine_output_filename(
                        paths["raw"], ext=sharding.get("format", "jsonl")
                    )
                    print(f"Flushed shard -> {output_file}")

            save_processed_urls(processed_path, processed)
            continue

        # --- Scraping do X (Twitter) desativado por enquanto ---
        # if source["type"] == "x_search":
        #     try:
        #         max_items = int(scraping["max_articles_per_source"])
        #
        #         pairs = search_recent_tweets(
        #             query=source["query"],
        #             max_results=max_items,
        #             pages=int(source.get("pages", 2)),
        #         )
        #     except Exception as e:
        #         print(f"[WARN] Failed X search for {source['name']}: {e}")
        #         continue
        #
        #     print(f"Discovered tweets: {len(pairs)}")
        #
        #     for tweet, author in pairs:
        #         record = normalize_x_record(source["name"], tweet, author)
        #
        #         # checkpoint: canonical_url ou fallback
        #         key = record.get("canonical_url") or f"x://status/{record.get('id','')}"
        #         if not key or key in processed:
        #             continue
        #
        #         if runtime["dry_run"]:
        #             print("[dry-run]", key)
        #             processed.add(key)
        #             continue
        #
        #         buffer.append(record)
        #         processed.add(key)
        #
        #         if len(buffer) >= items_per_shard:
        #             append_csv(output_file, buffer)
        #             save_processed_urls(processed_path, processed)
        #             buffer = []
        #             output_file, shard_id = determine_output_filename(
        #                 paths["raw"], ext=sharding.get("format", "jsonl")
        #             )
        #             print(f"Flushed shard -> {output_file}")
        #
        #         sleep(float(scraping["sleep_time"]))
        #
        #     save_processed_urls(processed_path, processed)
        #     continue

        print(f"Source type desconhecido: {source['type']}. Pulando.")
        continue

    if buffer and not runtime["dry_run"]:
        append_csv(output_file, buffer)
        save_processed_urls(processed_path, processed)
        print(f"Final flush -> {output_file}")


if __name__ == "__main__":
    main()
