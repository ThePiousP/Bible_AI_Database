#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill the `strongs_lexicon` table in concordance.db from STEP JSON files
(and/or a master lexicon JSON), without editing any existing modules.

- Scans a directory of STEP chapter JSONs (e.g., STEP_Genesis.*.json)
- Extracts Strong's IDs seen in tokens, along with lexicon fields:
    lemma, transliteration, pronunciation, pos, definition,
    kjv_translation_count, kjv_counts (as JSON), etymology, outline (as JSON)
- UPSERTS by strong_norm, preserving existing non-empty DB values
- Logs conflicts to CSV (if requested) for future manual review

Usage (POSIX):
  python backfill_strongs_lexicon.py \
      --db ./concordance.db \
      --step_dir ./ \
      --conflict_csv ./lexicon_conflicts.csv

Usage (Windows):
  python backfill_strongs_lexicon.py ^
      --db C:\BIBLE\concordance.db ^
      --step_dir .\ ^
      --conflict_csv .\lexicon_conflicts.csv

Optional:
  --lexicon_json path/to/master_strongs.json   # if you have a consolidated lexicon file
  --limit_files 100                            # scan at most N STEP files (useful for a pilot run)
  --dry_run                                    # parse & report only, no DB writes
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import platform
import sqlite3
import sys
from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

# -----------------------------
# Data model
# -----------------------------
FIELDS = [
    "strong_norm",              # key
    "lemma",
    "transliteration",
    "pronunciation",
    "pos",
    "definition",
    "kjv_translation_count",    # int
    "kjv_counts_json",          # JSON-encoded dict
    "etymology",
    "outline_json",             # JSON-encoded outline/list
]

@dataclass
class LexEntry:
    strong_norm: str
    lemma: Optional[str] = None
    transliteration: Optional[str] = None
    pronunciation: Optional[str] = None
    pos: Optional[str] = None
    definition: Optional[str] = None
    kjv_translation_count: Optional[int] = None
    kjv_counts_json: Optional[str] = None
    etymology: Optional[str] = None
    outline_json: Optional[str] = None

    def merge_prefer_existing(self, other: "LexEntry") -> Tuple["LexEntry", Dict[str, Tuple[str, str]]]:
        """
        Return a new LexEntry that prefers self's non-empty values.
        If self has empty and other has non-empty, take other.
        Track conflicts when both have *different* non-empty values.
        """
        new = LexEntry(strong_norm=self.strong_norm)
        conflicts: Dict[str, Tuple[str, str]] = {}
        for field in FIELDS:
            if field == "strong_norm":
                setattr(new, field, self.strong_norm)
                continue
            a = getattr(self, field)
            b = getattr(other, field)
            a_norm = normalize_field(a)
            b_norm = normalize_field(b)
            # Prefer non-empty 'a'
            if a_norm is not None and a_norm != "":
                setattr(new, field, a)
                # if b is also non-empty and different -> conflict
                if b_norm is not None and b_norm != "" and not equal_field(a, b):
                    conflicts[field] = (str(a), str(b))
            elif b_norm is not None and b_norm != "":
                setattr(new, field, b)
            else:
                setattr(new, field, a if a is not None else b)
        return new, conflicts


def normalize_field(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    s = str(v).strip()
    return s


def equal_field(a: Any, b: Any) -> bool:
    # Treat JSON-serializable structures equivalently when possible
    try:
        if isinstance(a, (dict, list)) or isinstance(b, (dict, list)):
            return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
        # normalize whitespace
        return normalize_field(a) == normalize_field(b)
    except Exception:
        return str(a).strip() == str(b).strip()


# -----------------------------
# DB helpers
# -----------------------------
def ensure_table(conn: sqlite3.Connection) -> None:
    """
    Ensure `strongs_lexicon` table exists with expected columns and a unique index on strong_norm.
    We DO NOT drop/alter existing data.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS strongs_lexicon (
            strong_norm TEXT PRIMARY KEY,
            lemma TEXT,
            transliteration TEXT,
            pronunciation TEXT,
            pos TEXT,
            definition TEXT,
            kjv_translation_count INTEGER,
            kjv_counts_json TEXT,
            etymology TEXT,
            outline_json TEXT
        )
    """)
    # Primary key covers uniqueness; if the table already exists without PK, add index:
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_strongs_lexicon_strong_norm ON strongs_lexicon(strong_norm)")


def fetch_existing(conn: sqlite3.Connection) -> Dict[str, LexEntry]:
    rows = conn.execute("SELECT {} FROM strongs_lexicon".format(", ".join(FIELDS))).fetchall()
    out: Dict[str, LexEntry] = {}
    for r in rows:
        out[r["strong_norm"]] = LexEntry(
            strong_norm=r["strong_norm"],
            lemma=r["lemma"],
            transliteration=r["transliteration"],
            pronunciation=r["pronunciation"],
            pos=r["pos"],
            definition=r["definition"],
            kjv_translation_count=r["kjv_translation_count"],
            kjv_counts_json=r["kjv_counts_json"],
            etymology=r["etymology"],
            outline_json=r["outline_json"],
        )
    return out


def upsert_entries(conn: sqlite3.Connection, entries: Iterable[LexEntry]) -> None:
    sql = f"""
        INSERT INTO strongs_lexicon ({", ".join(FIELDS)})
        VALUES ({", ".join("?" for _ in FIELDS)})
        ON CONFLICT(strong_norm) DO UPDATE SET
            lemma=COALESCE(excluded.lemma, lemma),
            transliteration=COALESCE(excluded.transliteration, transliteration),
            pronunciation=COALESCE(excluded.pronunciation, pronunciation),
            pos=COALESCE(excluded.pos, pos),
            definition=COALESCE(excluded.definition, definition),
            kjv_translation_count=COALESCE(excluded.kjv_translation_count, kjv_translation_count),
            kjv_counts_json=COALESCE(excluded.kjv_counts_json, kjv_counts_json),
            etymology=COALESCE(excluded.etymology, etymology),
            outline_json=COALESCE(excluded.outline_json, outline_json)
    """
    cur = conn.cursor()
    for e in entries:
        vals = tuple(asdict(e)[k] for k in FIELDS)
        cur.execute(sql, vals)
    conn.commit()


# -----------------------------
# STEP JSON parsing
# -----------------------------
# --- DROP-IN START: recursive STEP JSON discovery ---

import os, json, fnmatch

def _looks_like_step_json(path: str) -> bool:
    """
    Conservative check so we don't ingest random JSONs.
    Returns True if the JSON has keys typically present in STEP chapter files.
    We keep this very lightweight: open, read a small prefix, json.load, then inspect.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Common STEP chapter hints (any one is enough):
        #  - top-level "book" and "chapter"
        #  - top-level "verses" as list/dict
        #  - nested under something like {"step": { ... "verses": ...}}
        if isinstance(data, dict):
            if "verses" in data and isinstance(data["verses"], (list, dict)):
                return True
            if "book" in data and "chapter" in data:
                return True
            step = data.get("step") or data.get("STEP")
            if isinstance(step, dict) and "verses" in step:
                return True
        return False
    except Exception:
        return False


def iter_step_files(step_root: str, limit_files: Optional[int]) -> List[str]:
    """
    Recursively walk `step_root` and collect STEP chapter JSON files.

    We accept:
      - Filenames matching 'STEP_*.json' (preferred)
      - Otherwise any '*.json' that passes _looks_like_step_json()

    Results are returned sorted by path. `limit_files` (if set) truncates the list.
    """
    candidates: List[str] = []
    step_root = step_root or "."

    for root, _dirs, files in os.walk(step_root):
        # Prefer explicit STEP_* pattern first
        for name in files:
            if fnmatch.fnmatch(name, "STEP_*.json"):
                candidates.append(os.path.join(root, name))

        # Fall back to any .json that looks like a STEP chapter
        for name in files:
            if name.lower().endswith(".json"):
                full = os.path.join(root, name)
                # Skip if already captured as STEP_*.json
                if full in candidates:
                    continue
                if _looks_like_step_json(full):
                    candidates.append(full)

    # Deduplicate + sort
    seen = set()
    files = []
    for p in sorted(candidates):
        if p not in seen:
            files.append(p)
            seen.add(p)

    if limit_files is not None and limit_files >= 0:
        files = files[:limit_files]

    return files


def extract_entries_from_step_json(doc: Any) -> Dict[str, LexEntry]:
    """
    Walk a STEP chapter JSON (structure can vary) and collect lexicon entries by Strong's ID.
    We look for tokens that carry:
      - strong_norm / strongs / strong / id (normalized to H/G prefix + zero-padded)
      - plus any of: lemma, pos, definition, transliteration, pronunciation,
                    kjv_translation_count, kjv_counts, etymology, outline
    """
    collected: Dict[str, LexEntry] = {}

    def maybe_add(sid: Optional[str], token: Dict[str, Any]) -> None:
        sid_norm = normalize_strongs(sid)
        if not sid_norm:
            return
        entry = collected.get(sid_norm) or LexEntry(strong_norm=sid_norm)

        # map various possible field names
        lemma = token.get("lemma") or token.get("lexeme") or token.get("hebrew") or token.get("greek")
        translit = token.get("transliteration")
        pron = token.get("pronunciation")
        pos = token.get("pos") or token.get("part_of_speech")
        definition = token.get("definition") or token.get("def") or token.get("gloss")
        kjv_count = token.get("kjv_translation_count") or token.get("kjvCount") or token.get("kjv_count")
        kjv_counts = token.get("kjv_counts") or token.get("kjvCounts")
        etym = token.get("etymology")
        outline = token.get("outline") or token.get("sense_outline") or token.get("outline_of_biblical_usage")

        # Normalize numeric + JSON fields
        if kjv_count is not None:
            try:
                kjv_count = int(kjv_count)
            except Exception:
                kjv_count = None
        kjv_counts_json = json.dumps(kvj(kjv_counts), ensure_ascii=False) if kjv_counts is not None else None
        outline_json = json.dumps(outline, ensure_ascii=False) if outline is not None else None

        # Fill any new non-empty values into entry
        entry = choose_nonempty(entry, "lemma", lemma)
        entry = choose_nonempty(entry, "transliteration", translit)
        entry = choose_nonempty(entry, "pronunciation", pron)
        entry = choose_nonempty(entry, "pos", pos)
        entry = choose_nonempty(entry, "definition", definition)
        if kjv_count is not None:
            entry.kjv_translation_count = entry.kjv_translation_count or kjv_count
        entry = choose_nonempty(entry, "kjv_counts_json", kjv_counts_json)
        entry = choose_nonempty(entry, "etymology", etym)
        entry = choose_nonempty(entry, "outline_json", outline_json)

        collected[sid_norm] = entry

    def walk(node: Any):
        if isinstance(node, dict):
            # If this looks like a token, try to extract
            cand_sid = node.get("strong_norm") or node.get("strongs") or node.get("strong") or node.get("id")
            if cand_sid:
                maybe_add(cand_sid, node)
            # Also handle nested "lexicon" blobs under a token, e.g., node["lexicon"]={}
            lex_blob = node.get("lexicon")
            if isinstance(lex_blob, dict):
                # in some STEP variants, "lexicon" holds fields keyed by the strongs
                for k, v in lex_blob.items():
                    if isinstance(v, dict):
                        maybe_add(k, v)
            # Recurse
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        # else: scalar -> ignore

    walk(doc)
    return collected


def kvj(obj: Any) -> Any:
    """'kjv_counts' normalizer. Accept dict/list or fall back to None if not structured."""
    if isinstance(obj, (dict, list)):
        return obj
    try:
        # Sometimes stringified JSON
        return json.loads(obj)
    except Exception:
        return None


def normalize_strongs(sid: Optional[str]) -> Optional[str]:
    if not sid:
        return None
    s = str(sid).strip().upper()
    # Common forms: "H0430", "G2316", "H430", "0430", "2316"
    # Try to detect Hebrew (H) or Greek (G); default to leaving as-is if it already has prefix
    if s.startswith(("H", "G")):
        prefix = s[0]
        digits = "".join(ch for ch in s[1:] if ch.isdigit())
    else:
        # If there's a hint (e.g., field "hebrew"/"greek") we could detect here; for now, assume 'H' if 4 digits, else leave as-is.
        prefix = "H"  # conservative default; many OT tokens
        digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return s
    # Zero-pad to 4 digits (H0430); Strong's can have up to 4 digits typically
    digits = digits.zfill(4)
    return f"{prefix}{digits}"


def choose_nonempty(entry: LexEntry, field: str, candidate: Optional[Any]) -> LexEntry:
    val = getattr(entry, field)
    if val is None or str(val).strip() == "":
        if candidate is not None and str(candidate).strip() != "":
            setattr(entry, field, candidate)
    return entry


# -----------------------------
# Optional master lexicon JSON
# -----------------------------
def extract_entries_from_master_json(path: str) -> Dict[str, LexEntry]:
    """
    Accepts:
      - dict keyed by strongs_id -> {lemma, pos, ...}
      - or list of {strongs: "...", lemma: "...", ...}
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    out: Dict[str, LexEntry] = {}

    def add_entry(sid: str, payload: Dict[str, Any]):
        sid_norm = normalize_strongs(sid)
        if not sid_norm:
            return
        e = out.get(sid_norm) or LexEntry(strong_norm=sid_norm)
        # Map fields similar to STEP
        lemma = payload.get("lemma")
        translit = payload.get("transliteration")
        pron = payload.get("pronunciation")
        pos = payload.get("pos") or payload.get("part_of_speech")
        definition = payload.get("definition") or payload.get("def") or payload.get("gloss")
        kjv_count = payload.get("kjv_translation_count") or payload.get("kjvCount") or payload.get("kjv_count")
        kjv_counts = payload.get("kjv_counts") or payload.get("kjvCounts")
        etym = payload.get("etymology")
        outline = payload.get("outline") or payload.get("outline_of_biblical_usage")

        if kjv_count is not None:
            try:
                kjv_count = int(kjv_count)
            except Exception:
                kjv_count = None
        kjv_counts_json = json.dumps(kvj(kjv_counts), ensure_ascii=False) if kjv_counts is not None else None
        outline_json = json.dumps(outline, ensure_ascii=False) if outline is not None else None

        e = choose_nonempty(e, "lemma", lemma)
        e = choose_nonempty(e, "transliteration", translit)
        e = choose_nonempty(e, "pronunciation", pron)
        e = choose_nonempty(e, "pos", pos)
        e = choose_nonempty(e, "definition", definition)
        if kjv_count is not None:
            e.kjv_translation_count = e.kjv_translation_count or kjv_count
        e = choose_nonempty(e, "kjv_counts_json", kjv_counts_json)
        e = choose_nonempty(e, "etymology", etym)
        e = choose_nonempty(e, "outline_json", outline_json)

        out[sid_norm] = e

    if isinstance(data, dict):
        for sid, payload in data.items():
            if isinstance(payload, dict):
                add_entry(str(sid), payload)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                sid = item.get("strongs") or item.get("id") or item.get("strong_norm")
                if sid:
                    add_entry(str(sid), item)
    return out


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Backfill strongs_lexicon from STEP JSON and/or a master lexicon JSON.")
    default_db = r"C:\BIBLE\concordance.db" if platform.system().lower().startswith("win") else "./concordance.db"
    ap.add_argument("--db", default=default_db, help="Path to concordance.db")
    ap.add_argument("--step_dir", default=".", help="Directory containing STEP_*.json chapter files")
    ap.add_argument("--lexicon_json", default=None, help="Optional master Strong's JSON to ingest as well")
    ap.add_argument("--limit_files", type=int, default=None, help="Limit number of STEP files scanned (for a pilot run)")
    ap.add_argument("--conflict_csv", default=None, help="If set, write conflicts to this CSV")
    ap.add_argument("--dry_run", action="store_true", help="Parse and summarize only; do not write to DB")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: DB not found at {args.db}", file=sys.stderr)
        sys.exit(2)

    # Collect entries from STEP files
    step_files = iter_step_files(args.step_dir, args.limit_files)
    if not step_files and not args.lexicon_json:
        print("WARN: No STEP files found and no master lexicon JSON provided. Nothing to do.", file=sys.stderr)
        sys.exit(0)

    print(f"INFO: STEP files to scan: {len(step_files)}")
    collected: Dict[str, LexEntry] = {}

    def collect_from_entry_map(entry_map: Dict[str, LexEntry], source_tag: str, conflicts_log: List[Tuple[str, str, str, str]]) -> None:
        nonlocal collected
        for sid, new_entry in entry_map.items():
            if sid in collected:
                merged, conf = collected[sid].merge_prefer_existing(new_entry)
                collected[sid] = merged
                # record conflicts
                for field, (old, new) in conf.items():
                    conflicts_log.append((sid, field, old, new))
            else:
                collected[sid] = new_entry

    conflicts_log: List[Tuple[str, str, str, str]] = []

    # Scan STEP JSONs
    for i, path in enumerate(step_files, 1):
        try:
            with open(path, "r", encoding="utf-8") as f:
                doc = json.load(f)
            entry_map = extract_entries_from_step_json(doc)
            collect_from_entry_map(entry_map, os.path.basename(path), conflicts_log)
            if i % 25 == 0:
                print(f"INFO: Scanned {i}/{len(step_files)} files… collected so far: {len(collected)} entries")
        except Exception as e:
            print(f"WARN: Failed to parse {path}: {e}", file=sys.stderr)

    # Optional: master lexicon JSON
    if args.lexicon_json:
        if os.path.exists(args.lexicon_json):
            try:
                master = extract_entries_from_master_json(args.lexicon_json)
                collect_from_entry_map(master, os.path.basename(args.lexicon_json), conflicts_log)
                print(f"INFO: Merged master lexicon JSON entries: {len(master)}")
            except Exception as e:
                print(f"WARN: Failed to parse master lexicon JSON {args.lexicon_json}: {e}", file=sys.stderr)
        else:
            print(f"WARN: Master lexicon JSON not found: {args.lexicon_json}", file=sys.stderr)

    print(f"INFO: Collected Strong's entries: {len(collected)}")

    # Optional: write conflicts
    if args.conflict_csv:
        try:
            with open(args.conflict_csv, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["strong_norm", "field", "kept_value", "ignored_value"])
                for sid, fld, kept, ignored in conflicts_log:
                    w.writerow([sid, fld, kept, ignored])
            print(f"INFO: Wrote conflicts to {args.conflict_csv} (rows: {len(conflicts_log)})")
        except Exception as e:
            print(f"WARN: Could not write conflict CSV: {e}", file=sys.stderr)

    if args.dry_run:
        print("INFO: Dry run only; no DB writes performed.")
        return

    # Write to DB (UPSERT)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        ensure_table(conn)

        # Merge with existing DB rows (preserve DB non-empty values)
        existing = fetch_existing(conn)
        final_entries: List[LexEntry] = []
        final_conflicts: List[Tuple[str, str, str, str]] = []

        for sid, new_entry in collected.items():
            if sid in existing:
                merged, conf = existing[sid].merge_prefer_existing(new_entry)
                final_entries.append(merged)
                for field, (old, new) in conf.items():
                    final_conflicts.append((sid, field, old, new))
            else:
                final_entries.append(new_entry)

        if final_conflicts and not args.conflict_csv:
            print(f"WARN: {len(final_conflicts)} conflicts detected during DB-merge (run with --conflict_csv to capture).", file=sys.stderr)

        print(f"INFO: Upserting {len(final_entries)} entries into strongs_lexicon…")
        upsert_entries(conn, final_entries)

        # Post-write stats
        total = conn.execute("SELECT COUNT(*) AS n FROM strongs_lexicon").fetchone()["n"]
        nonnull_lemma = conn.execute("SELECT COUNT(*) AS n FROM strongs_lexicon WHERE lemma IS NOT NULL AND TRIM(lemma)<>''").fetchone()["n"]
        nonnull_def = conn.execute("SELECT COUNT(*) AS n FROM strongs_lexicon WHERE definition IS NOT NULL AND TRIM(definition)<>''").fetchone()["n"]
        print(f"INFO: strongs_lexicon rows now: {total} (lemma: {nonnull_lemma}, definition: {nonnull_def})")

        # Quick join check: how many tokens now have lemma via tokens_with_lexicon?
        # (If the view is defined as LEFT JOIN on strong_norm, this should rise above zero.)
        try:
            have_lemma = conn.execute("""
                SELECT COUNT(*) AS n
                FROM tokens_with_lexicon
                WHERE lemma IS NOT NULL AND TRIM(lemma) <> ''
            """).fetchone()["n"]
            print(f"INFO: tokens_with_lexicon rows with lemma now: {have_lemma}")
        except Exception:
            # some installs may lack the view name; ignore
            pass

    finally:
        conn.close()


if __name__ == "__main__":
    main()
