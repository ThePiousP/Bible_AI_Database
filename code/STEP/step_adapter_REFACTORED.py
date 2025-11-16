#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step_adapter.py (REFACTORED - Phase 2)
Main orchestrator with backward-compatible imports

BEFORE (Phase 1):
  - Single monolithic file (1474 lines)
  - Mixed responsibilities
  - No type hints
  - Hard to navigate and maintain

AFTER (Phase 2):
  - Split into 8 focused modules:
    1. step_constants.py - Book catalogs, OSIS codes
    2. step_normalization.py - Strong's/morph normalization
    3. step_enrichment.py - Strong's lexicon loading
    4. step_alignment.py - Text alignment, fuzzy matching
    5. step_parsers.py - Data shapes, HTML parsers
    6. step_export.py - Export functions, batch operations
    7. step_cli.py - Menu interfaces
    8. step_adapter.py - This file (orchestrator)

  - Full type hints throughout
  - Better error handling
  - Backward compatible (all imports still work)
  - Clear separation of concerns

BACKWARD COMPATIBILITY:
  All existing imports continue to work:
    from step_adapter import Token, Verse, export_chapter, batch_export_book, ...

Created: 2025-10-29 (Phase 2 Refactoring)
"""

import argparse
import re
from pathlib import Path
from typing import Optional

# ============================================================================
# Re-export all public APIs for backward compatibility
# ============================================================================

# Constants & Catalogs
from step_constants import (
    OLD_TESTAMENT_BOOKS,
    NEW_TESTAMENT_BOOKS,
    BOOK_CHAPTERS,
    BOOK_INDEX,
    BOOK_OSIS,
    is_valid_book,
    get_chapter_count,
    get_osis_code,
    get_book_index,
    is_old_testament,
    is_new_testament,
    get_all_books_in_order,
)

# Normalization
from step_normalization import (
    format_strongs_norm,
    normalize_strongs,
    normalize_morph,
    load_morph_map,
    decode_morph,
    reset_morph_cache,
)

# Enrichment
from step_enrichment import (
    strongs_key,
    collect_strongs_dirs,
    load_strongs_lexicon,
    normalize_kjv_counts,
    enrich_tokens_with_strongs,
    get_cached_lexicon,
    reset_lexicon_cache,
)

# Alignment
from step_alignment import (
    collapse,
    tidy_punct,
    is_ignorable,
    fuzzy_find,
    align_text_offsets,
    sort_tokens_for_json,
    vfrag_offsets,
)

# Parsers (Data Structures)
from step_parsers import (
    Token,
    Footnote,
    Verse,
    parse_with_selectolax,
    parse_with_bs4,
    parse_step_html,
)

# Export Functions
from step_export import (
    build_url,
    fetch_html,
    plain_from_html_bs4,
    tok_to_dict,
    export_chapter,
    open_log,
    log_message,
    batch_export_book,
    batch_export_full_bible,
)

# CLI
from step_cli import (
    load_config,
    set_field,
    prompt as _prompt,
    yn as _yn,
    settings_menu,
    run_menu,
)


# ============================================================================
# Backward Compatibility Aliases
# ============================================================================

# Rename CLI helpers to avoid conflicts (internal use)
def settings_menu_legacy():
    """Legacy wrapper for settings_menu()."""
    return settings_menu()


def run_menu_legacy():
    """Legacy wrapper for run_menu()."""
    return run_menu()


# ============================================================================
# Global Cache (Backward Compatibility)
# ============================================================================

# Legacy cache variables (now managed by step_enrichment.py)
_STRONGS_CACHE = None  # Use get_cached_lexicon() instead
_MORPH_MAP_CACHE = None  # Use load_morph_map() instead


# Backward-compatible function wrappers
def _format_strongs_norm(s: Optional[str]) -> Optional[str]:
    """Legacy wrapper - use format_strongs_norm() instead."""
    return format_strongs_norm(s)


def _strongs_key(s: str) -> Optional[str]:
    """Legacy wrapper - use strongs_key() instead."""
    return strongs_key(s)


def _collect_strongs_dirs(custom_dirs=None):
    """Legacy wrapper - use collect_strongs_dirs() instead."""
    return collect_strongs_dirs(custom_dirs)


def _load_strongs_lexicon(dir_hints=None, verbose=False):
    """Legacy wrapper - use load_strongs_lexicon() instead."""
    return load_strongs_lexicon(dir_hints, verbose)


def _enrich_tokens_with_strongs(tokens, strongs_index):
    """Legacy wrapper - use enrich_tokens_with_strongs() instead."""
    return enrich_tokens_with_strongs(tokens, strongs_index)


def _normalize_kjv_counts(raw):
    """Legacy wrapper - use normalize_kjv_counts() instead."""
    return normalize_kjv_counts(raw)


def _align_text_offsets(text_plain, tokens):
    """Legacy wrapper - use align_text_offsets() instead."""
    return align_text_offsets(text_plain, tokens)


def _sort_tokens_for_json(tokens):
    """Legacy wrapper - use sort_tokens_for_json() instead."""
    return sort_tokens_for_json(tokens)


def _vfrag_offsets(fragment_html, verse_html, start_idx):
    """Legacy wrapper - use vfrag_offsets() instead."""
    return vfrag_offsets(fragment_html, verse_html, start_idx)


def _prompt(msg: str, default: Optional[str] = None) -> str:
    """Legacy wrapper - use prompt() from step_cli instead."""
    from step_cli import prompt
    return prompt(msg, default)


def _yn(msg: str, default: bool) -> bool:
    """Legacy wrapper - use yn() from step_cli instead."""
    from step_cli import yn
    return yn(msg, default)


def _open_log(log_dir, book):
    """Legacy wrapper - use open_log() instead."""
    return open_log(log_dir, book)


def _log(log_path, msg):
    """Legacy wrapper - use log_message() instead."""
    return log_message(log_path, msg)


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """
    Command-line interface for STEP adapter.

    Usage:
        python step_adapter.py --menu
        python step_adapter.py --ref Gen.22 --out output/Gen.22.json
        python step_adapter.py --infile STEP_Gen22.html --out output.json
        python step_adapter.py --batch-book Gen --start 1 --end 50
    """
    ap = argparse.ArgumentParser(description="Export STEP chapter to structured JSON")
    ap.add_argument("--menu", action="store_true", help="Run interactive menu")
    ap.add_argument("--url", help="Full STEP URL (local/public)")
    ap.add_argument("--infile", help="Path to an already-saved STEP HTML file")
    ap.add_argument("--ref", help="OSIS ref, e.g., Gen.22 (used if --url not given)")
    ap.add_argument("--version", help="Version code (defaults from config)")
    ap.add_argument("--options", help="STEP options string (defaults from config)")
    ap.add_argument("--out", help="Output JSON path (default: output/json/<ref>.json)")
    ap.add_argument("--include-italics", choices=["true", "false"], help="Override config default")
    ap.add_argument("--parser", choices=["auto", "selectolax", "bs4"], help="Override parser default")

    # Batch options
    ap.add_argument("--batch-book", help="Export a whole book by code (e.g., Gen)")
    ap.add_argument("--start", type=int, help="Batch start chapter")
    ap.add_argument("--end", type=int, help="Batch end chapter")
    ap.add_argument("--source", choices=["url", "file"], help="Batch source mode")
    ap.add_argument("--html-dir", default=".", help="Dir for local STEP HTML when --source=file")
    ap.add_argument("--continue-on-error", choices=["true", "false"], help="Override config continue_on_error")
    ap.add_argument("--verbose", action="store_true", help="Verbose parser warnings")

    args = ap.parse_args()

    # If --menu or no args, run interactive menu
    if args.menu or not any([args.url, args.infile, args.ref, args.batch_book]):
        run_menu()
        return

    # Load config
    cfg = load_config()
    include_italics = cfg["include_italics_default"] if args.include_italics is None else (
        args.include_italics.lower() == "true"
    )
    parser = cfg["parser_default"] if args.parser is None else args.parser
    version = args.version or cfg["version_default"]
    options = args.options or cfg["options_default"]
    output_dir = cfg["output_dir"]
    continue_on_error = cfg["continue_on_error"] if args.continue_on_error is None else (
        args.continue_on_error.lower() == "true"
    )

    # Batch export
    if args.batch_book:
        start = args.start or cfg["batch_defaults"]["start_chapter"]
        end = args.end or cfg["batch_defaults"]["end_chapter"]
        source = args.source or "url"

        res = batch_export_book(
            book=args.batch_book,
            start=start,
            end=end,
            source_mode=source,
            version=version,
            options=options,
            html_dir=args.html_dir,
            output_dir=output_dir,
            include_italics=include_italics,
            parser=parser,
            continue_on_error=continue_on_error,
            log_dir=cfg["log_dir"],
            verbose=args.verbose
        )
        print(f"Batch finished. OK={len(res['ok'])}, Failed={len(res['failed'])}\nLog: {res['log']}")
        return

    # Single export via CLI
    if args.url:
        source = args.url
        m = re.search(r"reference=([A-Za-z0-9\.\-:_]+)", source)
        ref_hint = m.group(1) if m else None
    elif args.infile:
        source = args.infile
        ref_hint = Path(args.infile).stem.replace("STEP_", "")
    else:
        ref_hint = args.ref
        source = build_url(version, args.ref, options)

    out_path = args.out or str((Path(output_dir) / f"{(ref_hint or 'STEP')}.json").resolve())
    print(f"Exporting:\n  source: {source}\n  out:    {out_path}\n  include_italics={include_italics}\n  parser={parser}")

    payload = export_chapter(
        source,
        out_path,
        include_italics=include_italics,
        parser=parser,
        verbose=args.verbose
    )
    print(f"Done. Verses: {payload['verse_count']}")


if __name__ == "__main__":
    main()
