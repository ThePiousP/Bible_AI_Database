#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
silver_export.py
Main orchestrator for silver NER dataset export

BEFORE (Phase 1):
  - All logic in export_ner_silver.py (901 lines)
  - Mixed responsibilities
  - No type hints

AFTER (Phase 2):
  - Dedicated export orchestrator
  - Full type hints
  - Clean separation of concerns
  - Backward compatible imports

Created: 2025-10-29 (Phase 2 Refactoring)
"""

import argparse
import json
import os
import platform
import random
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm not installed
    def tqdm(iterable, **kwargs):
        return iterable

# Import from split modules
from silver_data_models import Token, Verse, Span, NERExample, SchemaInfo
from silver_label_rules import LabelRules
from silver_alignment import build_spans_with_phrases, calculate_alignment_stats


# ============================================================================
# Schema Detection
# ============================================================================

def has_column(conn: sqlite3.Connection, table: str, col: str) -> bool:
    """Check if table has column."""
    try:
        cur = conn.execute(f"PRAGMA table_info({table})")
        cols = [r[1].lower() for r in cur.fetchall()]
        return col.lower() in cols
    except Exception:
        return False


def detect_schema(conn: sqlite3.Connection, text_prefer: str = "auto") -> SchemaInfo:
    """
    Detect database schema and determine which text column to use.

    Args:
        conn: Database connection
        text_prefer: "auto", "clean", or "plain"

    Returns:
        SchemaInfo object

    Logic:
        - If text_prefer="clean" and text_clean exists → use text_clean
        - If text_prefer="plain" and text_plain exists → use text_plain
        - If text_prefer="auto" → prefer text_clean if exists, else text_plain
        - Fall back to available column
    """
    has_plain = has_column(conn, "verses", "text_plain")
    has_clean = has_column(conn, "verses", "text_clean")

    # Determine which column to use
    if text_prefer == "clean":
        text_col = "text_clean" if has_clean else ("text_plain" if has_plain else "text")
    elif text_prefer == "plain":
        text_col = "text_plain" if has_plain else ("text_clean" if has_clean else "text")
    else:  # auto
        text_col = "text_clean" if has_clean else ("text_plain" if has_plain else "text")

    return SchemaInfo(
        has_text_plain=has_plain,
        has_text_clean=has_clean,
        text_prefer=text_prefer,
        text_column=text_col
    )


# ============================================================================
# Data Fetching
# ============================================================================

def fetch_verses(
    conn: sqlite3.Connection,
    schema: SchemaInfo,
    holdout_books: Optional[List[str]] = None
) -> List[Verse]:
    """
    Fetch all verses from database.

    Args:
        conn: Database connection
        schema: Schema information
        holdout_books: Optional list of book names to exclude

    Returns:
        List of Verse objects
    """
    # Build SQL query
    sql = f"""
        SELECT
            v.id AS verse_id,
            b.book_name,
            c.chapter_number,
            v.verse_num,
            v.{schema.text_column} AS verse_text
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        ORDER BY b.id, c.chapter_number, v.verse_num
    """

    cursor = conn.execute(sql)
    verses: List[Verse] = []

    for row in cursor.fetchall():
        verse_id, book_name, chapter, verse_num, text = row

        # Skip holdout books
        if holdout_books and book_name in holdout_books:
            continue

        verses.append(Verse(
            verse_id=verse_id,
            book=book_name,
            chapter=chapter,
            verse=verse_num,
            text=text or "",
            tokens=[],
            align_spans=[]
        ))

    return verses


def attach_tokens(conn: sqlite3.Connection, verses: List[Verse]) -> None:
    """
    Attach tokens to verses (in-place).

    Args:
        conn: Database connection
        verses: List of Verse objects (modified in-place)
    """
    verse_map = {v.verse_id: v for v in verses}

    sql = """
        SELECT
            verse_id,
            text,
            strong_norm,
            token_idx
        FROM tokens
        ORDER BY verse_id, token_idx
    """

    cursor = conn.execute(sql)
    for row in cursor.fetchall():
        verse_id, surface, strongs, token_idx = row
        if verse_id in verse_map:
            verse_map[verse_id].tokens.append(Token(
            surface=surface or "",
            strongs_id=strongs,
            lemma=None,  # Not in your database
            pos=None     # Not in your database
        ))


# ============================================================================
# Stratified Split
# ============================================================================

def stratified_split(
    items: List[Dict[str, Any]],
    by_key: str,
    ratios: Tuple[float, float, float],
    seed: int = 13,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Stratify items by key and split into train/dev/test.

    Args:
        items: List of dictionaries
        by_key: Key to stratify by (e.g., "book")
        ratios: (train, dev, test) ratios (must sum to 1.0)
        seed: Random seed for reproducibility

    Returns:
        Tuple of (train, dev, test) lists

    Example:
        >>> items = [{"book": "Genesis", "text": "..."}, ...]
        >>> train, dev, test = stratified_split(items, "book", (0.8, 0.1, 0.1), seed=13)
    """
    rng = random.Random(seed)
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for item in items:
        buckets[str(item.get(by_key, "UNKNOWN"))].append(item)

    train_all: List[Dict[str, Any]] = []
    dev_all: List[Dict[str, Any]] = []
    test_all: List[Dict[str, Any]] = []

    for stratum, group in buckets.items():
        rng.shuffle(group)
        n = len(group)
        train_size = int(n * ratios[0])
        dev_size = int(n * ratios[1])

        train_all.extend(group[:train_size])
        dev_all.extend(group[train_size:train_size+dev_size])
        test_all.extend(group[train_size+dev_size:])

    return train_all, dev_all, test_all


# ============================================================================
# JSONL Writing
# ============================================================================

def write_jsonl(path: str, rows: List[Dict[str, Any]], show_progress: bool = True) -> None:
    """Write list of dicts to JSONL file."""
    filename = os.path.basename(path)
    with open(path, "w", encoding="utf-8") as f:
        iterator = tqdm(rows, desc=f"Writing {filename}", unit="line") if show_progress and len(rows) > 1000 else rows
        for row in iterator:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ============================================================================
# Main Export Function
# ============================================================================

def export_silver_dataset(
    db_path: str,
    rules_file: str,
    output_dir: str,
    text_prefer: str = "auto",
    seed: int = 13,
    ratios: Tuple[float, float, float] = (0.8, 0.1, 0.1),
    holdout_books: Optional[List[str]] = None,
    holdout_name: str = "domain_holdout",
    require_clean: bool = False,
    align_report: bool = False,
    label_on_miss: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export silver NER dataset from concordance database.

    Args:
        db_path: Path to SQLite database
        rules_file: Path to label_rules.yml
        output_dir: Output directory for JSONL files
        text_prefer: "auto", "clean", or "plain"
        seed: Random seed for splits
        ratios: (train, dev, test) split ratios
        holdout_books: Books to exclude from training
        holdout_name: Name for holdout split
        require_clean: Require text_clean column
        align_report: Print alignment statistics
        label_on_miss: Default label for unmatched tokens

    Returns:
        Dictionary with statistics

    Example:
        >>> stats = export_silver_dataset(
        ...     db_path="concordance.db",
        ...     rules_file="label_rules.yml",
        ...     output_dir="silver_out",
        ...     seed=13
        ... )
        >>> print(f"Train: {stats['train_count']}, Dev: {stats['dev_count']}")
    """
    # Load config
    with open(rules_file, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Connect to database
    conn = sqlite3.connect(db_path)

    # Detect schema
    schema = detect_schema(conn, text_prefer)
    print(f"Using text column: verses.{schema.text_column}")

    if require_clean and not schema.has_text_clean:
        print("ERROR: require_clean=True but text_clean column not found", file=sys.stderr)
        sys.exit(1)

    # Load label rules
    rules = LabelRules(cfg, label_on_miss=label_on_miss)
    print(f"Loaded {len(rules.enabled_labels)} enabled labels")

    # Fetch verses
    print("Fetching verses...")
    verses = fetch_verses(conn, schema, holdout_books)
    print(f"Fetched {len(verses)} verses")

    # Attach tokens
    print("Attaching tokens...")
    attach_tokens(conn, verses)
    total_tokens = sum(len(v.tokens) for v in verses)
    print(f"Attached {total_tokens} tokens")

    # Build spans
    print("Building labeled spans...")
    examples: List[Dict[str, Any]] = []

    for verse in tqdm(verses, desc="Building spans", unit="verse"):
        spans = build_spans_with_phrases(verse, rules)
        if spans:  # Only include verses with at least one span
            examples.append({
                "text": verse.text,
                "spans": [{"start": s.start, "end": s.end, "label": s.label} for s in spans],
                "meta": {
                    "book": verse.book,
                    "chapter": verse.chapter,
                    "verse": verse.verse,
                    "verse_id": verse.verse_id
                }
            })

    print(f"\nCreated {len(examples)} examples with spans")

    # Alignment report
    if align_report:
        stats = calculate_alignment_stats(verses)
        print(f"\nAlignment Statistics:")
        print(f"  Total tokens: {stats['total_tokens']:,}")
        print(f"  Aligned: {stats['aligned']:,}")
        print(f"  Unaligned: {stats['unaligned']:,}")
        print(f"  Success rate: {stats['success_rate']*100:.2f}%")

    # Split into train/dev/test
    print(f"\nSplitting data (seed={seed})...")
    train, dev, test = stratified_split(examples, "book", ratios, seed)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Write JSONL files
    train_path = os.path.join(output_dir, "train.jsonl")
    dev_path = os.path.join(output_dir, "dev.jsonl")
    test_path = os.path.join(output_dir, "test.jsonl")

    write_jsonl(train_path, train)
    write_jsonl(dev_path, dev)
    write_jsonl(test_path, test)

    print(f"\nWrote {len(train)} train examples to {train_path}")
    print(f"Wrote {len(dev)} dev examples to {dev_path}")
    print(f"Wrote {len(test)} test examples to {test_path}")

    # Close connection
    conn.close()

    return {
        "total_verses": len(verses),
        "total_tokens": total_tokens,
        "total_examples": len(examples),
        "train_count": len(train),
        "dev_count": len(dev),
        "test_count": len(test),
        "text_column": schema.text_column
    }


# ============================================================================
# CLI Entry Point
# ============================================================================

def main() -> None:
    """Command-line interface."""
    parser = argparse.ArgumentParser(description="Export silver NER dataset from concordance.db")
    parser.add_argument("--db", required=True, help="Path to concordance.db")
    parser.add_argument("--rules", required=True, help="Path to label_rules.yml")
    parser.add_argument("--outdir", default="./silver_out", help="Output directory")
    parser.add_argument("--text-prefer", choices=["auto", "clean", "plain"], default="auto")
    parser.add_argument("--seed", type=int, default=13, help="Random seed")
    parser.add_argument("--holdout-books", nargs="*", help="Books to hold out")
    parser.add_argument("--require-clean", action="store_true")
    parser.add_argument("--align-report", action="store_true")
    parser.add_argument("--label-on-miss", help="Default label for unmatched tokens")

    args = parser.parse_args()

    # Default DB path fallback
    db_path = args.db
    if not os.path.exists(db_path):
        default_win = "C:\\BIBLE\\concordance.db" if platform.system().lower().startswith("win") else "./concordance.db"
        if os.path.exists(default_win):
            db_path = default_win
            print(f"Using default: {db_path}")

    stats = export_silver_dataset(
        db_path=db_path,
        rules_file=args.rules,
        output_dir=args.outdir,
        text_prefer=args.text_prefer,
        seed=args.seed,
        holdout_books=args.holdout_books,
        require_clean=args.require_clean,
        align_report=args.align_report,
        label_on_miss=args.label_on_miss
    )

    print("\n" + "=" * 60)
    print("Export complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
