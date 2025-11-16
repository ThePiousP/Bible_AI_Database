#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step_export.py
Export functions and batch operations for STEP data

BEFORE (Phase 1):
  - Export functions in step_adapter.py (lines 1019-1260)
  - Mixed responsibilities
  - No type hints
  - Logging mixed with export logic

AFTER (Phase 2):
  - Dedicated export module
  - Full type hints
  - Better error handling
  - Separated logging and export concerns
  - Batch export capabilities

Created: 2025-10-29 (Phase 2 Refactoring)
"""

import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import asdict

# Import from other STEP modules
from step_parsers import parse_step_html, Token, Verse
from step_enrichment import get_cached_lexicon, enrich_tokens_with_strongs
from step_alignment import sort_tokens_for_json, align_text_offsets, collapse, tidy_punct
from step_constants import BOOK_CHAPTERS, BOOK_OSIS, BOOK_INDEX
from step_normalization import format_strongs_norm


# ============================================================================
# Helper: OSIS to Full Book Name
# ============================================================================

# Create reverse lookup: OSIS code -> Full book name
OSIS_TO_BOOK = {v: k for k, v in BOOK_OSIS.items()}


# ============================================================================
# URL Construction & HTML Fetching
# ============================================================================

def build_url(version: str, ref: str, options: str) -> str:
    """
    Build STEP URL for fetching chapter data.

    Args:
        version: Bible version code (e.g., "KJV", "NKJV")
        ref: OSIS reference (e.g., "Gen.22", "Matt.5")
        options: STEP options string (e.g., "NHVUG")

    Returns:
        Full URL string

    Example:
        >>> build_url("KJV", "Gen.1", "NHVUG")
        'http://localhost:8989/?q=version=KJV@reference=Gen.1&options=NHVUG'
    """
    v = version.strip()
    r = ref.strip()
    o = options.strip()
    return f"http://localhost:8989/?q=version={v}@reference={r}&options={o}"


def fetch_html(url: str) -> str:
    """
    Fetch HTML from STEP URL using Playwright.

    Args:
        url: Full URL to fetch

    Returns:
        HTML content as string

    Raises:
        ImportError: If playwright is not installed
        Exception: If page load fails
    """
    from playwright.sync_api import sync_playwright

    print(f"[FETCH] Navigating to: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Track all network requests to see what's being loaded
        requests = []
        page.on("request", lambda request: requests.append(request.url))

        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(500)  # Reduced from 1500ms to 500ms
        html = page.content()
        browser.close()

    # Print first 5 network requests to see what's being loaded
    print(f"[FETCH] Network requests made ({len(requests)} total):")
    for req in requests[:5]:
        print(f"  - {req}")
    if len(requests) > 5:
        print(f"  ... and {len(requests) - 5} more")

    return html


# ============================================================================
# Plain Text Extraction (Helper)
# ============================================================================

def plain_from_html_bs4(html_text: str) -> str:
    """
    Extract plain text from HTML using BeautifulSoup.

    Removes verse numbers and footnotes for clean plain text.

    Args:
        html_text: HTML string

    Returns:
        Plain text string

    Example:
        >>> plain_from_html_bs4("<span>Hello<sup class='note'>1</sup></span>")
        'Hello'
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return ""

    soup = BeautifulSoup(html_text or "", "html.parser")

    # Remove verse numbers
    for sel in [
        "span.verseNumber",
        "span.verse-num",
        "sup.verseNumber",
        "sup.verse-num",
        "a.verseNumber",
        "a.verse-num"
    ]:
        for el in soup.select(sel):
            el.decompose()

    # Remove inline footnotes
    for sel in [
        "sup.note",
        "span.inlineNote",
        "a.sideNote",
        "a[notetype]"
    ]:
        for el in soup.select(sel):
            el.decompose()

    # Extract text
    txt = soup.get_text(" ", strip=True)
    txt = collapse(txt)
    txt = tidy_punct(txt)
    return txt


# ============================================================================
# Token Serialization
# ============================================================================

def tok_to_dict(t: Token) -> Dict[str, Any]:
    """
    Convert Token dataclass to dictionary for JSON export.

    Args:
        t: Token object

    Returns:
        Dictionary representation
    """
    d = asdict(t)

    # Re-normalize Strong's number for consistency
    if d.get("strong_norm"):
        d["strong_norm"] = format_strongs_norm(d["strong_norm"])

    return d


# ============================================================================
# Chapter Export
# ============================================================================

def export_chapter(
    url_or_file: str,
    out_json_path: str,
    include_italics: bool = True,
    include_morph_gloss: bool = True,
    parser: str = "auto",
    verbose: bool = False,
    strongs_dirs: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Export a single chapter to JSON with full linguistic annotations.

    Args:
        url_or_file: STEP URL or path to saved HTML file
        out_json_path: Output JSON file path
        include_italics: Include italics tokens
        include_morph_gloss: Include morphology glosses
        parser: "auto", "selectolax", or "bs4"
        verbose: Print diagnostic info
        strongs_dirs: Custom Strong's lexicon directories

    Returns:
        Dictionary payload (also written to file)

    Example:
        >>> export_chapter(
        ...     "STEP_Gen22.html",
        ...     "output/Gen.22.json",
        ...     verbose=True
        ... )
        {'source': 'STEP_Gen22.html', 'verse_count': 24, ...}
    """
    # Load HTML
    if url_or_file.lower().startswith(("http://", "https://")):
        html = fetch_html(url_or_file)
    else:
        html = Path(url_or_file).read_text(encoding="utf-8")

    # Parse HTML
    verses = parse_step_html(
        html,
        include_italics=include_italics,
        parser=parser,
        verbose=verbose
    )

    # Strong's enrichment (cached)
    lexicon = get_cached_lexicon(dir_hints=strongs_dirs, verbose=verbose)
    if not lexicon and verbose:
        print("[strongs] WARNING: No Strong's entries loaded. Check cache/STRONGS directory.")

    if lexicon:
        for v in verses:
            enrich_tokens_with_strongs(v.tokens, lexicon)

    # Build payload
    payload = {
        "source": url_or_file,
        "verse_count": len(verses),
        "verses": []
    }

    for v in verses:
        # Sort tokens by verse-relative offsets
        tok_sorted = sort_tokens_for_json(v.tokens)

        # Derive clean plain text if needed
        v_plain = v.text_plain if (v.text_plain and v.text_plain.strip()) else \
            plain_from_html_bs4(v.verse_html or "")

        # Align token spans to plain text
        align_text_offsets(v_plain, tok_sorted)

        payload["verses"].append({
            "ref": v.ref,
            "verse_num": v.verse_num,
            "text_plain": v_plain,
            "verse_html": v.verse_html,
            "tokens": [tok_to_dict(t) for t in tok_sorted],
            "footnotes": [asdict(fn) for fn in v.footnotes],
        })

    # Write JSON
    outp = Path(out_json_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return payload


# ============================================================================
# Batch Export Logging
# ============================================================================

def open_log(log_dir: Path, book: str) -> Path:
    """
    Create a timestamped log file.

    Args:
        log_dir: Log directory path
        book: Book name for log filename

    Returns:
        Path to created log file
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p = log_dir / f"batch_{book}_{ts}.log"
    p.write_text("", encoding="utf-8")
    return p


def log_message(log_path: Path, msg: str) -> None:
    """
    Log a message to file and console.

    Args:
        log_path: Log file path
        msg: Message to log
    """
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}\n"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)
    print(msg)


# ============================================================================
# Batch Export - Single Book
# ============================================================================

def batch_export_book(
    book: str,
    start: int,
    end: int,
    source_mode: str,
    version: str,
    options: str,
    html_dir: str,
    output_dir: str,
    include_italics: bool,
    parser: str,
    continue_on_error: bool,
    log_dir: str,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Export multiple chapters of a single book.

    Args:
        book: OSIS book code (e.g., "Gen", "Matt")
        start: Starting chapter number
        end: Ending chapter number (inclusive)
        source_mode: "url" or "file"
        version: Bible version code
        options: STEP options string
        html_dir: Directory with saved HTML files (if source_mode="file")
        output_dir: Output directory for JSON files
        include_italics: Include italics tokens
        parser: Parser to use
        continue_on_error: Continue if a chapter fails
        log_dir: Log directory
        verbose: Verbose output

    Returns:
        Dictionary with "ok" and "failed" lists, plus "log" path

    Example:
        >>> batch_export_book(
        ...     book="Gen",
        ...     start=1,
        ...     end=5,
        ...     source_mode="file",
        ...     version="KJV",
        ...     options="NHVUG",
        ...     html_dir="cache/html",
        ...     output_dir="output/json",
        ...     include_italics=True,
        ...     parser="auto",
        ...     continue_on_error=True,
        ...     log_dir="output/logs"
        ... )
        {'ok': ['Gen.1', 'Gen.2', ...], 'failed': [], 'log': '...'}
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Convert OSIS code to full book name for output filenames
    book_name = OSIS_TO_BOOK.get(book, book)

    # Check if this is a single-chapter book
    total_chapters = BOOK_CHAPTERS.get(book_name, 1)

    log_path = open_log(Path(log_dir), book)
    log_message(log_path, f"BEGIN book={book} ({book_name}) {start}..{end} source={source_mode} parser={parser} italics={include_italics}")

    results = {"ok": [], "failed": []}

    for ch in range(start, end + 1):
        # Single-chapter books: use just the OSIS code (e.g., "Obad" not "Obad.1")
        # Otherwise STEP returns only verse 1 instead of the whole chapter
        if total_chapters == 1:
            ref = book
        else:
            ref = f"{book}.{ch}"

        out_path = str((out_dir / f"STEP_{book_name}.{ch}.json").resolve())

        try:
            if source_mode == "url":
                src = build_url(version, ref, options)
            else:
                html_path = Path(html_dir) / f"STEP_{book}{ch}.html"
                if not html_path.exists():
                    raise FileNotFoundError(str(html_path))
                src = str(html_path)

            log_message(log_path, f"EXPORT {ref} -> {out_path}")
            export_chapter(src, out_path, include_italics=include_italics, parser=parser, verbose=verbose)
            results["ok"].append(ref)

        except Exception as e:
            tb = traceback.format_exc(limit=1).strip().replace("\n", " | ")
            log_message(log_path, f"ERROR {ref}: {e.__class__.__name__}: {e} :: {tb}")
            results["failed"].append({"ref": ref, "error": f"{e.__class__.__name__}: {e}"})

            if not continue_on_error:
                log_message(log_path, "ABORT on first error (continue_on_error=False)")
                break

    log_message(log_path, f"DONE ok={len(results['ok'])} failed={len(results['failed'])}")
    results["log"] = str(log_path.resolve())
    return results


# ============================================================================
# Batch Export - Full Bible
# ============================================================================

def batch_export_full_bible(
    source_mode: str,
    version: str,
    options: str,
    html_dir: str,
    output_dir: str,
    include_italics: bool,
    parser: str,
    continue_on_error: bool,
    log_dir: str,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Export every chapter of every book (all 66 books).

    Output paths: <output_dir>/<BookName>/STEP_<BookName>.<chapter>.json
    Source (if mode='file'): <html_dir>/STEP_<OSIS><chapter>.html

    Args:
        source_mode: "url" or "file"
        version: Bible version code
        options: STEP options string
        html_dir: HTML directory (if source_mode="file")
        output_dir: Output directory
        include_italics: Include italics tokens
        parser: Parser to use
        continue_on_error: Continue on errors
        log_dir: Log directory
        verbose: Verbose output

    Returns:
        Dictionary with "ok" and "failed" lists, plus "log" path

    Example:
        >>> batch_export_full_bible(
        ...     source_mode="file",
        ...     version="KJV",
        ...     options="NHVUG",
        ...     html_dir="cache/html",
        ...     output_dir="output/json",
        ...     include_italics=True,
        ...     parser="auto",
        ...     continue_on_error=True,
        ...     log_dir="output/logs"
        ... )
        {'ok': ['Genesis.1', 'Genesis.2', ...], 'failed': [], 'log': '...'}
    """
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    log_path = open_log(Path(log_dir), "FULL_BIBLE")
    log_message(log_path, f"BEGIN FULL_BIBLE source={source_mode} parser={parser} italics={include_italics}")

    results = {"ok": [], "failed": []}

    # Iterate in canonical order (Genesis → Revelation)
    for book in sorted(BOOK_INDEX.keys(), key=lambda b: BOOK_INDEX[b]):
        osis = BOOK_OSIS.get(book, book)
        chapters = BOOK_CHAPTERS[book]

        # Per-book directory
        book_out_dir = out_root / book
        book_out_dir.mkdir(parents=True, exist_ok=True)

        for ch in range(1, chapters + 1):
            # Single-chapter books: use just the OSIS code (e.g., "Obad" not "Obad.1")
            # Otherwise STEP returns only verse 1 instead of the whole chapter
            if chapters == 1:
                ref = osis
            else:
                ref = f"{osis}.{ch}"

            out_path = str((book_out_dir / f"STEP_{book}.{ch}.json").resolve())

            try:
                if source_mode == "url":
                    src = build_url(version, ref, options)
                else:
                    html_path = Path(html_dir) / f"STEP_{osis}{ch}.html"
                    if not html_path.exists():
                        raise FileNotFoundError(str(html_path))
                    src = str(html_path)

                log_message(log_path, f"EXPORT {book} {ch}/{chapters} ({ref}) -> {out_path}")
                export_chapter(
                    src,
                    out_path,
                    include_italics=include_italics,
                    include_morph_gloss=True,
                    parser="auto",
                    verbose=True,
                    strongs_dirs=["cache/STRONGS"]
                )
                results["ok"].append(f"{book}.{ch}")

            except Exception as e:
                tb = traceback.format_exc(limit=1).strip().replace("\n", " | ")
                log_message(log_path, f"ERROR {book}.{ch}: {e.__class__.__name__}: {e} :: {tb}")
                results["failed"].append({"ref": f"{book}.{ch}", "error": f"{e.__class__.__name__}: {e}"})

                if not continue_on_error:
                    log_message(log_path, "ABORT on first error (continue_on_error=False)")
                    log_message(log_path, f"DONE ok={len(results['ok'])} failed={len(results['failed'])}")
                    results["log"] = str(log_path.resolve())
                    return results

    log_message(log_path, f"DONE ok={len(results['ok'])} failed={len(results['failed'])}")
    results["log"] = str(log_path.resolve())
    return results


if __name__ == "__main__":
    print("STEP Export Module")
    print("=" * 60)
    print("Functions: export_chapter, batch_export_book, batch_export_full_bible")
    print("\n✓ Export module loaded successfully!")
