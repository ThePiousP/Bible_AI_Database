#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step_download_html.py
Download all Bible chapter HTML files from localhost:8989

This script ONLY downloads HTML files - no parsing.
After downloading, use the main script with source_mode="file" for fast processing.
"""

from pathlib import Path
from playwright.sync_api import sync_playwright
from step_constants import BOOK_CHAPTERS, BOOK_OSIS, BOOK_INDEX
from step_config import load_config
from datetime import datetime


def download_all_html(
    version: str = None,
    options: str = None,
    output_dir: str = None,
    wait_ms: int = 500
):
    """
    Download all Bible chapter HTML files from localhost:8989.

    Args:
        version: Bible version (e.g., "KJV"), defaults to config value
        options: STEP options string (e.g., "NHVUG"), defaults to config value
        output_dir: Directory to save HTML files, defaults to config value
        wait_ms: Milliseconds to wait after page load
    """
    # Load config values if not provided
    cfg = load_config()
    if version is None:
        version = cfg.get("version_default", "KJV")
    if options is None:
        options = cfg.get("options_default", "NHVUG")
    if output_dir is None:
        output_dir = cfg.get("html_cache_dir", "cache/html")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    total_chapters = sum(BOOK_CHAPTERS.values())
    print(f"Starting HTML download for {total_chapters} chapters...")
    print(f"Version: {version}, Options: {options}")
    print(f"Output: {out_dir}")
    print(f"=" * 60)

    start_time = datetime.now()
    downloaded = 0
    failed = 0

    # Launch browser ONCE and reuse for all chapters
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Iterate through all books in canonical order
        for book in sorted(BOOK_INDEX.keys(), key=lambda b: BOOK_INDEX[b]):
            osis = BOOK_OSIS.get(book, book)
            chapters = BOOK_CHAPTERS[book]

            print(f"\n{book} ({chapters} chapters):")

            for ch in range(1, chapters + 1):
                # Single-chapter books: use just the OSIS code (e.g., "Obad" not "Obad.1")
                # Otherwise STEP returns only verse 1 instead of the whole chapter
                if chapters == 1:
                    ref = osis
                else:
                    ref = f"{osis}.{ch}"

                url = f"http://localhost:8989/?q=version={version}@reference={ref}&options={options}"
                output_file = out_dir / f"STEP_{osis}{ch}.html"

                try:
                    # Navigate and wait
                    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                    page.wait_for_timeout(wait_ms)

                    # Save HTML
                    html = page.content()
                    output_file.write_text(html, encoding="utf-8")

                    downloaded += 1
                    progress = (downloaded / total_chapters) * 100
                    print(f"  [{downloaded:4d}/{total_chapters}] {progress:5.1f}% - {ref:15s} -> {output_file.name}")

                except Exception as e:
                    failed += 1
                    print(f"  [ERROR] {ref}: {e}")

        browser.close()

    # Summary
    elapsed = datetime.now() - start_time
    print(f"\n" + "=" * 60)
    print(f"Download complete!")
    print(f"  Success: {downloaded}")
    print(f"  Failed:  {failed}")
    print(f"  Time:    {elapsed}")
    print(f"  Output:  {out_dir.resolve()}")
    print(f"\nNext step: Run the main script with source_mode='file' and html_dir='{output_dir}'")


if __name__ == "__main__":
    import argparse

    # Load config for defaults
    cfg = load_config()

    ap = argparse.ArgumentParser(description="Download all Bible HTML from localhost:8989")
    ap.add_argument("--version", default=None, help=f"Bible version code (default: {cfg.get('version_default', 'KJV')})")
    ap.add_argument("--options", default=None, help=f"STEP options string (default: {cfg.get('options_default', 'NHVUG')})")
    ap.add_argument("--output", default=None, help=f"Output directory for HTML files (default: {cfg.get('html_cache_dir', 'cache/html')})")
    ap.add_argument("--wait", type=int, default=500, help="Wait time in milliseconds after page load")

    args = ap.parse_args()

    download_all_html(
        version=args.version,
        options=args.options,
        output_dir=args.output,
        wait_ms=args.wait
    )
