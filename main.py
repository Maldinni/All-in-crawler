from time import sleep

from src.utils.parsing import parse_args, load_config
from src.utils.checkpoints import load_processed_urls, save_processed_urls
from src.utils.discovery import discover_article_urls_listing, build_listing_pages, discover_g1_urls_follow_see_more, discover_urls_with_wp_pagination
from src.utils.extraction import extract_with_retry
from src.utils.io import ensure_dirs, determine_output_filename, append_csv

from src.utils.X.x_search import search_recent_tweets
from src.utils.X.x_extraction import normalize_x_record

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

    output_file, shard_id = determine_output_filename(paths["output"], ext=sharding.get("format", "jsonl"))
    buffer = []
    items_per_shard = int(sharding.get("items_per_shard", 200))

    # filtra uma fonte, se pedido
    if runtime["source_filter"]:
        sources = [s for s in sources if s["name"] == runtime["source_filter"]]

    for source in sources:
        print(f'\n=== Source: {source["name"]} ({source["type"]}) ===')

        if source["type"] == "x_search":
            try:
                pairs = search_recent_tweets(
                    query=source["query"],
                    max_results=int(source.get("max_results", 50)),
                    pages=int(source.get("pages", 2)),
                )
            except Exception as e:
                print(f"[WARN] Failed X search for {source['name']}: {e}")
                continue

            print(f"Discovered tweets: {len(pairs)}")

            for tweet, author in pairs:
                record = normalize_x_record(source["name"], tweet, author)

                # checkpoint: canonical_url ou fallback
                key = record.get("canonical_url") or f"x://status/{record.get('id','')}"
                if not key or key in processed:
                    continue

                if runtime["dry_run"]:
                    print("[dry-run]", key)
                    processed.add(key)
                    continue

                buffer.append(record)
                processed.add(key)

                if len(buffer) >= items_per_shard:
                    append_csv(output_file, buffer)
                    save_processed_urls(processed_path, processed)
                    buffer = []
                    output_file, shard_id = determine_output_filename(
                        paths["output"], ext=sharding.get("format", "jsonl")
                    )
                    print(f"Flushed shard -> {output_file}")

                sleep(float(scraping["sleep_time"]))

            save_processed_urls(processed_path, processed)
            continue

        print(f"Source type desconhecido: {source['type']}. Pulando.")
        continue

    if buffer and not runtime["dry_run"]:
        append_csv(output_file, buffer)
        save_processed_urls(processed_path, processed)
        print(f"Final flush -> {output_file}")


if __name__ == "__main__":
    main()
