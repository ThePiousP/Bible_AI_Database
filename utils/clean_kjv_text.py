#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clean_kjv_text.py — Safely create verses.text_clean and populate it from verses.text_plain with configurable cleaning rules.

Features
- Makes a timestamped backup of the DB before any writes.
- Adds verses.text_clean column if missing (TEXT, nullable).
- Cleans text with conservative rules aimed at removing markup/artefacts while preserving verse punctuation and casing.
- Removes translator-note tails and margin markers (▼, etc.) to end of line.
- Normalizes ellipsis (…) to '...' for consistent tokenization.
- Dry-run mode prints a diff-style preview of first N changed rows.
- Optional --where filter and --limit for partial runs.
- Idempotent: re-running will overwrite text_clean with newly cleaned text (unless --skip-existing is set).

Usage
  python clean_kjv_text.py --db ./concordance.db --dry-run
  python clean_kjv_text.py --db ./concordance.db --commit

Recommended first: run --dry-run to preview, then run --commit when satisfied.
"""

from __future__ import annotations
import argparse, datetime, os, re, sqlite3, sys, unicodedata
from typing import Tuple, List

CLEANING_PROFILE = {
    "normalize_unicode": True,     # NFKC
    "strip_html_tags": True,       # remove any <...> tags that slipped in
    "unescape_basic_entities": True,  # &amp; &lt; &gt; &quot; &#39;
    "remove_brackets": True,       # [] and {} around words/phrases (footnote/markup artifacts)
    "drop_editorial_markers": True, # [a], [b], [1], {1}, etc.
    "drop_note_tails_by_marker": True,  # remove from first ▼/▲/◆/◊/※/* to end
    "drop_lang_note_tails": True,       # remove from ': Heb./Gr./Chald.' to end
    "normalize_ellipsis": True,    # … -> ...
    "collapse_spaces": True,       # collapse runs of whitespace to single space
    "trim": True,
}

HTML_TAG_RE   = re.compile(r"<[^>]+>")
BASIC_ENTS    = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&#39;": "'",
    "&apos;": "'",
    "&nbsp;": " ",
}
# Footnote/editorial markers like [a], [b], [1], {a}, {12}
EDITORIAL_RE  = re.compile(r"(\[[A-Za-z]\]|\[\d+\]|\{[A-Za-z]\}|\{\d+\})")
# Lone balanced square/curly brackets (but avoid removing real verse content inside parentheses)
BRACKETS_RE   = re.compile(r"[\[\]\{\}]")
# Normalize any weird whitespace (NBSP etc.) to normal spaces
WS_ANY_RE     = re.compile(r"\s+")
# Remove from first margin/note marker (e.g., ' ▼ ▼ ...') to end
NOTE_MARKER_TAIL_RE = re.compile(r"\s*[▼▲◆◊※*].*$", re.DOTALL)
# Remove translator-note tails like ': Heb. …', ': Gr. …', ': Chald. …' (case-insensitive)
LANG_NOTE_TAIL_RE = re.compile(r"[:;]\s*(Heb\.|Gr\.|Chald(?:ee)?\.)\s.*$", re.IGNORECASE | re.DOTALL)

def clean_text(s: str, profile = CLEANING_PROFILE) -> str:
    if s is None:
        return s
    out = s

    if profile.get("normalize_unicode", True):
        # NFKC: e.g., fancy quotes unify to compatibility forms
        out = unicodedata.normalize("NFKC", out)

    if profile.get("strip_html_tags", True):
        out = HTML_TAG_RE.sub("", out)

    if profile.get("unescape_basic_entities", True):
        for k, v in BASIC_ENTS.items():
            out = out.replace(k, v)

    if profile.get("drop_editorial_markers", True):
        out = EDITORIAL_RE.sub("", out)

    if profile.get("remove_brackets", True):
        # Remove stray []{} but leave parentheses alone
        out = BRACKETS_RE.sub("", out)

    # Apply tail removals BEFORE whitespace collapsing so we don't keep pieces
    if profile.get("drop_note_tails_by_marker", True):
        # remove from the first marker to end
        out = NOTE_MARKER_TAIL_RE.sub("", out, count=1)

    if profile.get("drop_lang_note_tails", True):
        out = LANG_NOTE_TAIL_RE.sub("", out, count=1)

    if profile.get("normalize_ellipsis", True):
        out = out.replace("…", "...")

    if profile.get("collapse_spaces", True):
        out = WS_ANY_RE.sub(" ", out)

    if profile.get("trim", True):
        out = out.strip()

    return out

def add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, coltype: str = "TEXT") -> None:
    cur = conn.execute(f"PRAGMA table_info({table})")
    cols = [row[1].lower() for row in cur.fetchall()]
    if column.lower() not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
        conn.commit()

def backup_db(path: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{path}.bak_{ts}"
    with open(path, "rb") as src, open(backup_path, "wb") as dst:
        dst.write(src.read())
    return backup_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Path to concordance.db")
    ap.add_argument("--table", default="verses")
    ap.add_argument("--source-col", default="text_plain")
    ap.add_argument("--target-col", default="text_clean")
    ap.add_argument("--where", default="", help="Optional SQL WHERE clause to restrict rows (e.g., \"book_id=1\")")
    ap.add_argument("--limit", type=int, default=0, help="Optional row limit for preview/partial runs")
    ap.add_argument("--dry-run", action="store_true", help="Preview changes only; no writes")
    ap.add_argument("--commit", action="store_true", help="Write changes to DB")
    ap.add_argument("--skip-existing", action="store_true", help="Do not overwrite rows where target-col is non-empty")
    ap.add_argument("--preview-n", type=int, default=50, help="Show first N changed rows in dry-run")
    args = ap.parse_args()

    if not (args.dry_run ^ args.commit):
        print("ERROR: choose exactly one of --dry-run or --commit", file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(args.db):
        print(f"ERROR: DB not found: {args.db}", file=sys.stderr)
        sys.exit(2)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        # Build SELECT
        where = f"WHERE {args.where}" if args.where.strip() else ""
        limit = f"LIMIT {args.limit}" if args.limit and args.limit > 0 else ""

        # Ensure target column exists
        add_column_if_missing(conn, args.table, args.target_col, "TEXT")

        # Pull rows to process
        sel_sql = f"""
        SELECT id, {args.source_col} AS src, {args.target_col} AS tgt
        FROM {args.table}
        {where}
        ORDER BY id
        {limit}
        """
        rows = list(conn.execute(sel_sql))
        if not rows:
            print("No rows selected.")
            return

        changed: List[Tuple[int, str, str, str]] = []
        same = 0
        for r in rows:
            src = r["src"]
            tgt = r["tgt"]
            if src is None:
                continue
            new = clean_text(src)
            # decide whether to write
            if args.skip_existing and (tgt is not None and str(tgt).strip() != ""):
                continue
            if tgt is None or new != tgt:
                changed.append((r["id"], src, tgt, new))
            else:
                same += 1

        if args.dry_run:
            print(f"DRY-RUN: {len(changed)} rows would change; {same} unchanged/skipped.")
            for (rid, src, tgt, new) in changed[:args.preview_n]:
                def show(s): 
                    s = s if s is not None else ""
                    s = s.replace("\n", "⏎")
                    return s
                print("---")
                print(f"id={rid}")
                print(f" src: {show(src)}")
                print(f" new: {show(new)}")
                if tgt not in (None, ""):
                    print(f" prev target: {show(tgt)}")
            return

        # COMMIT path: backup then write
        backup_path = backup_db(args.db)
        print(f"Backup written: {backup_path}")

        upd_sql = f"UPDATE {args.table} SET {args.target_col} = ? WHERE id = ?"
        with conn:
            conn.executemany(upd_sql, [(new, rid) for (rid, _src, _tgt, new) in changed])
        print(f"Updated {len(changed)} rows. Done.")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
