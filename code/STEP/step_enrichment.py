#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step_enrichment.py
Strong's lexicon loading and token enrichment for STEP data

BEFORE (Phase 1):
  - Enrichment functions in step_adapter.py (lines 138-274)
  - No type hints
  - Global cache (_STRONGS_CACHE)
  - Limited error handling

AFTER (Phase 2):
  - Dedicated enrichment module
  - Full type hints
  - Better path discovery
  - Structured KJV counts parsing
  - Clear error messages

Created: 2025-10-29 (Phase 2 Refactoring)
"""

import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from step_parsers import Token  # Avoid circular import


# ============================================================================
# Strong's Number Utilities
# ============================================================================

def strongs_key(s: str) -> Optional[str]:
    """
    Normalize H/G key to canonical H#### or G#### format (zero-padded to 4).

    Args:
        s: Strong's number string

    Returns:
        Normalized key (e.g., "H0430", "G5624"), or None if invalid

    Example:
        >>> strongs_key("H430")
        'H0430'
        >>> strongs_key("g1")
        'G0001'
    """
    if not s:
        return None

    s = s.strip().upper()
    head = s[:1]
    digits = ''.join(ch for ch in s[1:] if ch.isdigit())

    if head not in ("H", "G") or not digits:
        return None

    return f"{head}{int(digits):04d}"


# ============================================================================
# Strong's Directory Discovery
# ============================================================================

def collect_strongs_dirs(custom_dirs: Optional[List[str]] = None) -> List[Path]:
    """
    Build a search list for Strong's JSON folders.

    Priority:
      1. User-provided custom directories
      2. Common default locations
      3. Current directory

    Args:
        custom_dirs: Optional list of custom directory paths

    Returns:
        List of Path objects to search (deduplicated)

    Default search paths:
      - cache/STRONGS (Phase 1 standard)
      - strongs_json
      - strongs
      - STRONGS
      - lexicon
      - data/strongs
      - . (current directory)
    """
    defaults = [
        Path("cache/STRONGS"),      # Phase 1 standard location
        Path("strongs_json"),
        Path("strongs"),
        Path("STRONGS"),
        Path("lexicon"),
        Path("data/strongs"),
        Path("."),
    ]

    out: List[Path] = []

    # Add custom directories first (highest priority)
    if custom_dirs:
        out.extend([Path(d) for d in custom_dirs])

    # Add defaults
    out.extend(defaults)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[Path] = []

    for p in out:
        try:
            key = str(p.resolve()).lower()
        except Exception:
            key = str(p).lower()

        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique


# ============================================================================
# Strong's Lexicon Loading
# ============================================================================

def load_strongs_lexicon(
    dir_hints: Optional[List[str]] = None,
    verbose: bool = False
) -> Dict[str, Dict[str, Any]]:
    """
    Recursively load Strong's entries from *.json files.

    Accepts:
      - Single-object files (with 'strongs_number' field)
      - List of objects (each with 'strongs_number' field)

    Args:
        dir_hints: Optional custom directories to search
        verbose: Print diagnostic info during loading

    Returns:
        Dictionary mapping Strong's numbers (e.g., "H0430") to metadata

    Example:
        >>> lexicon = load_strongs_lexicon(verbose=True)
        [strongs] scanned dirs: cache/STRONGS, strongs
        [strongs] files scanned: 8718, entries loaded: 8674
    """
    cache: Dict[str, Dict[str, Any]] = {}
    candidates = collect_strongs_dirs(dir_hints)
    loaded_files = 0
    scanned_dirs: List[Path] = []

    for base in candidates:
        if not base.exists() or not base.is_dir():
            continue

        scanned_dirs.append(base)

        # Recursive scan for *.json files
        for json_path in base.rglob("*.json"):
            try:
                obj = json.loads(json_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError, OSError):
                continue  # Skip invalid JSON files

            def _ingest(rec: Dict[str, Any]) -> None:
                """Ingest a single Strong's record into cache."""
                key = strongs_key(rec.get("strongs_number") or json_path.stem)
                if not key:
                    return

                cache[key] = {
                    "lemma": rec.get("lemma"),
                    "transliteration": rec.get("transliteration"),
                    "pronunciation": rec.get("pronunciation"),
                    "pos": rec.get("pos"),
                    "definition": rec.get("definition"),
                    "kjv_translation_count": rec.get("kjv_translation_count"),
                    "etymology": rec.get("etymology"),
                    "outline": rec.get("outline") if isinstance(rec.get("outline"), list) else None,
                }

            # Handle both single-object and array files
            if isinstance(obj, dict):
                _ingest(obj)
                loaded_files += 1
            elif isinstance(obj, list):
                any_ingested = False
                for rec in obj:
                    if isinstance(rec, dict):
                        _ingest(rec)
                        any_ingested = True
                if any_ingested:
                    loaded_files += 1

    if verbose:
        if scanned_dirs:
            print(f"[strongs] scanned dirs: {', '.join(str(d) for d in scanned_dirs)}")
        print(f"[strongs] files scanned: {loaded_files}, entries loaded: {len(cache)}")

    return cache


# ============================================================================
# KJV Translation Count Parsing
# ============================================================================

def normalize_kjv_counts(raw: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    """
    Parse KJV translation count strings into structured format.

    Args:
        raw: Raw KJV count string

    Returns:
        List of {"gloss": str, "count": int} dicts, or None if empty

    Example:
        >>> normalize_kjv_counts("after (454x), follow (78x)")
        [{"gloss": "after", "count": 454}, {"gloss": "follow", "count": 78}]
    """
    if not raw:
        return None

    text = str(raw).strip().strip(".")

    # Split on semicolons or commas (permissive splitting)
    parts = [
        p.strip()
        for p in re.split(r"\s*;\s*|\s*,\s*(?=[^)\]]*(?:\(|$))", text)
        if p.strip()
    ]

    out: List[Dict[str, Any]] = []

    for seg in parts:
        # Find last integer in segment
        nums = re.findall(r"(\d+)\s*(?:x\b)?", seg)
        count = int(nums[-1]) if nums else None

        # Extract gloss: everything before first '('
        gloss = re.split(r"\(", seg, 1)[0]
        gloss = re.sub(r"[\s,:]+$", "", gloss).strip()
        gloss = gloss or None

        if gloss or count is not None:
            out.append({"gloss": gloss, "count": count})

    return out or None


# ============================================================================
# Token Enrichment
# ============================================================================

def enrich_tokens_with_strongs(
    tokens: List[Any],
    strongs_index: Dict[str, Dict[str, Any]]
) -> None:
    """In-place enrichment of Token objects from Strong's lexicon."""
    for t in tokens:
        key = strongs_key(t.strong_norm) if t.strong_norm else None
        if not key:
            continue

        meta = strongs_index.get(key)
        if not meta:
            continue

        # Enrich only missing fields
        if not t.lemma and meta.get("lemma"):
            t.lemma = meta.get("lemma")
        if not t.transliteration and meta.get("transliteration"):
            t.transliteration = meta.get("transliteration")
        if not t.pronunciation and meta.get("pronunciation"):
            t.pronunciation = meta.get("pronunciation")
        if not t.pos and meta.get("pos"):
            t.pos = meta.get("pos")
        if not t.definition and meta.get("definition"):
            t.definition = meta.get("definition")
        if not t.kjv_translation_count and meta.get("kjv_translation_count"):
            t.kjv_translation_count = meta.get("kjv_translation_count")
        if t.kjv_counts is None:
            t.kjv_counts = normalize_kjv_counts(t.kjv_translation_count)
        if not t.etymology and meta.get("etymology"):
            t.etymology = meta.get("etymology")
        if t.outline is None and meta.get("outline") is not None:
            t.outline = meta.get("outline")


# ============================================================================
# Global Cache
# ============================================================================

_STRONGS_CACHE: Optional[Dict[str, Dict[str, Any]]] = None


def get_cached_lexicon(
    dir_hints: Optional[List[str]] = None,
    verbose: bool = False
) -> Dict[str, Dict[str, Any]]:
    """Get cached Strong's lexicon (loads on first call)."""
    global _STRONGS_CACHE
    if _STRONGS_CACHE is None:
        _STRONGS_CACHE = load_strongs_lexicon(dir_hints=dir_hints, verbose=verbose)
    return _STRONGS_CACHE


def reset_lexicon_cache() -> None:
    """Reset the global Strong's cache."""
    global _STRONGS_CACHE
    _STRONGS_CACHE = None


if __name__ == "__main__":
    print("STEP Enrichment Module")
    print("=" * 60)
    lexicon = load_strongs_lexicon(verbose=True)
    print(f"\nLoaded {len(lexicon)} Strong's entries")
    print("\n✓ Enrichment module loaded successfully!")
