# menu_batch.py
# Tiny console menu that wraps step_adapter.export_chapter()
# Run:  python menu_batch.py

import sys
from pathlib import Path
from datetime import datetime

# Import your adapter
import step_adapter as SA  # must be in the same folder or on PYTHONPATH

# Defaults (you can tweak live from the menu)
STATE = {
    "version": "KJV",
    "options": "NHVUG",
    "include_italics": True,
    "allow_bs4": False,
    "base_url": "http://localhost:8989",
    "output_dir": str(SA.OUTPUT_DIR),  # uses your config.json default
}

def build_url(version: str, ref: str, options: str) -> str:
    return f"{STATE['base_url']}/?q=version={version}@reference={ref}&options={options}"

def scrape_ref(ref: str):
    """Scrape a single OSIS ref like 'Gen.22'."""
    url = build_url(STATE["version"], ref, STATE["options"])
    out_path = Path(STATE["output_dir"]) / f"{ref}.json"
    print(f"\n[SCRAPE] {ref}\n  URL: {url}\n  OUT: {out_path}")
    try:
        payload = SA.export_chapter(
            url_or_file=url,
            out_json_path=str(out_path),
            save_snapshot=True,
            allow_bs4=STATE["allow_bs4"],
            include_italics=STATE["include_italics"],
        )
        print(f"  ✔ Done. Verses: {payload['verse_count']}")
    except Exception as e:
        print(f"  ✖ Error: {e}")

def scrape_book_range(book: str, ch_start: int, ch_end: int):
    """Scrape a range within one book, e.g., book='Gen', 1..50."""
    for ch in range(ch_start, ch_end + 1):
        ref = f"{book}.{ch}"
        scrape_ref(ref)

def scrape_list(refs_csv: str):
    """Scrape a comma-separated list of OSIS refs, e.g., 'Gen.22,Gen.23,John.1'."""
    refs = [r.strip() for r in refs_csv.split(",") if r.strip()]
    for ref in refs:
        scrape_ref(ref)

def toggle_include_italics():
    STATE["include_italics"] = not STATE["include_italics"]
    print(f"  include_italics = {STATE['include_italics']}")

def toggle_allow_bs4():
    STATE["allow_bs4"] = not STATE["allow_bs4"]
    print(f"  allow_bs4 = {STATE['allow_bs4']}")

def set_version():
    v = input("Enter version (e.g., KJV, ESV): ").strip() or STATE["version"]
    STATE["version"] = v
    print(f"  version = {STATE['version']}")

def set_options():
    o = input("Enter STEP options string (e.g., NHVUG): ").strip() or STATE["options"]
    STATE["options"] = o
    print(f"  options = {STATE['options']}")

def set_output_dir():
    p = input(f"Output dir (current: {STATE['output_dir']}): ").strip()
    if p:
        Path(p).mkdir(parents=True, exist_ok=True)
        STATE["output_dir"] = p
    print(f"  output_dir = {STATE['output_dir']}")

def set_base_url():
    b = input(f"Base URL (current: {STATE['base_url']}, e.g., http://localhost:8989): ").strip()
    if b:
        STATE["base_url"] = b.rstrip("/")
    print(f"  base_url = {STATE['base_url']}")

def menu():
    while True:
        print("\n=== STEP Scraper Menu ===")
        print(" 1) Scrape single chapter")
        print(" 2) Scrape range of chapters in a book")
        print(" 3) Scrape list of refs (comma-separated)")
        print(" 4) Settings")
        print(" 5) Show current settings")
        print(" 0) Exit")
        choice = input("Select: ").strip()

        if choice == "1":
            book = input("Book (e.g., Gen, Exo, John): ").strip()
            ch   = input("Chapter (number): ").strip()
            if not (book and ch.isdigit()):
                print("  ✖ Please enter a book and a numeric chapter.")
                continue
            scrape_ref(f"{book}.{int(ch)}")

        elif choice == "2":
            book = input("Book (e.g., Gen): ").strip()
            a = input("Start chapter: ").strip()
            b = input("End chapter: ").strip()
            if not (book and a.isdigit() and b.isdigit()):
                print("  ✖ Please enter a book and two numeric chapter values.")
                continue
            scrape_book_range(book, int(a), int(b))

        elif choice == "3":
            refs = input("Refs (e.g., Gen.22,Gen.23,John.1): ").strip()
            if not refs:
                print("  ✖ Please enter at least one ref.")
                continue
            scrape_list(refs)

        elif choice == "4":
            print("\n--- Settings ---")
            print(" a) Toggle include_italics")
            print(" b) Toggle allow_bs4 (fallback)")
            print(" c) Set version")
            print(" d) Set options")
            print(" e) Set output dir")
            print(" f) Set base URL")
            print(" x) Back")
            s = input("Select setting: ").strip().lower()
            if   s == "a": toggle_include_italics()
            elif s == "b": toggle_allow_bs4()
            elif s == "c": set_version()
            elif s == "d": set_options()
            elif s == "e": set_output_dir()
            elif s == "f": set_base_url()
            else: pass

        elif choice == "5":
            print("\nCurrent settings:")
            for k, v in STATE.items():
                print(f"  - {k}: {v}")

        elif choice == "0":
            print("Bye.")
            break
        else:
            print("  ✖ Invalid choice.")

if __name__ == "__main__":
    print(f"STEP Scraper Console — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Make sure STEP is running (e.g., http://localhost:8989)")
    try:
        menu()
    except KeyboardInterrupt:
        print("\nInterrupted. Bye.")
        sys.exit(0)
