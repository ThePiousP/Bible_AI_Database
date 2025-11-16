# concordance_tools/strongs_batch_scraper.py
import os
import json
import time
from .strongs_scraper import scrape_strongs_entry  # ✅ Relative import fixed

# === CONFIG ===
OUTPUT_DIR = "output/concordance"
LOG_DIR = "output/logs"
PROGRESS_FILE = os.path.join(LOG_DIR, "progress.json")
COMPLETED_FILE = os.path.join(LOG_DIR, "completed_ids.json")
FAILED_FILE = os.path.join(LOG_DIR, "failed_ids.json")

RATE_LIMIT = 2.0  # seconds between requests
MAX_ENTRIES_PER_RUN = None  # Set to None for no cap
MODE = "ALL"  # Options: "H", "G", or "ALL"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def load_json_list(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_json_list(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_next_strongs_ids(mode):
    if mode == "H":
        return [f"H{i}" for i in range(1, 8675)]
    elif mode == "G":
        return [f"G{i}" for i in range(1, 5625)]
    else:
        return [f"H{i}" for i in range(1, 8675)] + [f"G{i}" for i in range(1, 5625)]


def scrape_batch():
    completed = set(load_json_list(COMPLETED_FILE))
    failed = set(load_json_list(FAILED_FILE))
    all_ids = get_next_strongs_ids(MODE)
    to_scrape = [s for s in all_ids if s not in completed and s not in failed]

    scraped = 0
    for strongs_id in to_scrape:
        out_path = os.path.join(OUTPUT_DIR, f"{strongs_id}.json")

        if os.path.exists(out_path):
            completed.add(strongs_id)
            continue

        print(f"\n⏳ Scraping {strongs_id}...")
        result = scrape_strongs_entry(strongs_id)
        if result:
            completed.add(strongs_id)
        else:
            failed.add(strongs_id)

        save_json_list(sorted(completed), COMPLETED_FILE)
        save_json_list(sorted(failed), FAILED_FILE)

        scraped += 1
        if MAX_ENTRIES_PER_RUN and scraped >= MAX_ENTRIES_PER_RUN:
            print(f"\n✅ Reached max scrape limit for this run: {MAX_ENTRIES_PER_RUN}")
            break

        time.sleep(RATE_LIMIT)

    print("\n🎉 Scraping session complete.")
    print(f"  ✔ Total scraped this run: {scraped}")
    print(f"  📄 Completed: {len(completed)} | ❌ Failed: {len(failed)}")


if __name__ == "__main__":
    scrape_batch()
