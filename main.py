from time import sleep

from src.utils.parsing import parse_args, load_config
from src.utils.checkpoints import load_processed_urls, save_processed_urls
from src.utils.discovery import discover_article_urls_listing
from src.utils.extraction import extract_with_retry
from src.utils.io import ensure_dirs, determine_output_filename, append_csv


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

        if source["type"] != "listing":
            print("Protótipo atual só suporta type=listing. Pulando.")
            continue

        listing_url = source["url"]
        allow_domains = source.get("allow_domains")
        try:
            urls = discover_article_urls_listing(
                listing_url=listing_url,
                allow_domains=allow_domains,
                user_agent=scraping["user_agent"],
                timeout_sec=int(scraping["timeout_sec"]),
            )
        except Exception as e:
            print(f"[WARN] Failed to discover URLs for {source['name']}: {e}")
            continue

        # limita por fonte
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
                float(scraping["sleep_time"])
            )


            # se falhar, marca como processado ou não? (decisão)
            # no protótipo, eu NÃO marcaria como processado se falhou
            if not data or not data.get("text"):
                continue

            data["source"] = source["name"]
            buffer.append(data)

            processed.add(url)

            if len(buffer) >= items_per_shard:
                append_csv(output_file, buffer)
                save_processed_urls(processed_path, processed)
                buffer = []
                output_file, shard_id = determine_output_filename(paths["output"], ext=sharding.get("format", "jsonl"))
                print(f"Flushed shard -> {output_file}")

            sleep(float(scraping["sleep_time"]))

        save_processed_urls(processed_path, processed)

    if buffer and not runtime["dry_run"]:
        append_csv(output_file, buffer)
        save_processed_urls(processed_path, processed)
        print(f"Final flush -> {output_file}")


if __name__ == "__main__":
    main()
