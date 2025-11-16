#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Load STEP JSON exports into SQLite with canonical order and clean token indexing.

Fixes baked in:
- Canonical insertion order (Genesis -> Revelation).
- token_idx re-assigned per verse by (vhtml_start, original_idx) to keep offsets monotonic.
- Preserve original order in tokens.original_token_idx.
- Keep empty-surface tokens in 'tokens', but provide a 'tokens_visible' view for downstream NER.
- Adds useful indexes (incl. verse_id, vhtml_start) and optional FTS5 over verses.text_plain.

Input layout (flexible names):
  cache\STEP_BIBLE\
    STEP_Genesis\
      STEP_Genesis.1.json
      STEP_Genesis.2.json
      ...
    STEP_Exodus\
      STEP_Exodus.1.json
      ...

Run:
  python load_step_json_to_sqlite.py
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# -----------------------------
# CONFIG
# -----------------------------

DB_PATH = "concordance.db"                 # new or overwrite existing
INPUT_ROOT = Path(r"cache\STEP_BIBLE")     # your input root

CREATE_VERSES_FTS = True                   # set False to skip FTS5 table/build

# -----------------------------
# CANON / ORDER
# -----------------------------

BOOK_INDEX: Dict[str, int] = {
    "Genesis": 1, "Exodus": 2, "Leviticus": 3, "Numbers": 4, "Deuteronomy": 5,
    "Joshua": 6, "Judges": 7, "Ruth": 8, "1 Samuel": 9, "2 Samuel": 10,
    "1 Kings": 11, "2 Kings": 12, "1 Chronicles": 13, "2 Chronicles": 14,
    "Ezra": 15, "Nehemiah": 16, "Esther": 17, "Job": 18, "Psalms": 19,
    "Proverbs": 20, "Ecclesiastes": 21, "Song of Solomon": 22, "Isaiah": 23,
    "Jeremiah": 24, "Lamentations": 25, "Ezekiel": 26, "Daniel": 27, "Hosea": 28,
    "Joel": 29, "Amos": 30, "Obadiah": 31, "Jonah": 32, "Micah": 33, "Nahum": 34,
    "Habakkuk": 35, "Zephaniah": 36, "Haggai": 37, "Zechariah": 38, "Malachi": 39,
    "Matthew": 40, "Mark": 41, "Luke": 42, "John": 43, "Acts": 44, "Romans": 45,
    "1 Corinthians": 46, "2 Corinthians": 47, "Galatians": 48, "Ephesians": 49,
    "Philippians": 50, "Colossians": 51, "1 Thessalonians": 52, "2 Thessalonians": 53,
    "1 Timothy": 54, "2 Timothy": 55, "Titus": 56, "Philemon": 57, "Hebrews": 58,
    "James": 59, "1 Peter": 60, "2 Peter": 61, "1 John": 62, "2 John": 63,
    "3 John": 64, "Jude": 65, "Revelation": 66
}

OSIS: Dict[str, str] = {
    "Genesis": "Gen", "Exodus": "Exo", "Leviticus": "Lev", "Numbers": "Num", "Deuteronomy": "Deut",
    "Joshua": "Josh", "Judges": "Judg", "Ruth": "Ruth", "1 Samuel": "1Sam", "2 Samuel": "2Sam",
    "1 Kings": "1Kgs", "2 Kings": "2Kgs", "1 Chronicles": "1Chr", "2 Chronicles": "2Chr",
    "Ezra": "Ezra", "Nehemiah": "Neh", "Esther": "Est", "Job": "Job", "Psalms": "Psa",
    "Proverbs": "Prov", "Ecclesiastes": "Eccl", "Song of Solomon": "Song", "Isaiah": "Isa",
    "Jeremiah": "Jer", "Lamentations": "Lam", "Ezekiel": "Ezek", "Daniel": "Dan", "Hosea": "Hos",
    "Joel": "Joel", "Amos": "Amos", "Obadiah": "Obad", "Jonah": "Jonah", "Micah": "Mic",
    "Nahum": "Nah", "Habakkuk": "Hab", "Zephaniah": "Zeph", "Haggai": "Hag", "Zechariah": "Zech",
    "Malachi": "Mal", "Matthew": "Matt", "Mark": "Mark", "Luke": "Luke", "John": "John",
    "Acts": "Acts", "Romans": "Rom", "1 Corinthians": "1Cor", "2 Corinthians": "2Cor",
    "Galatians": "Gal", "Ephesians": "Eph", "Philippians": "Phil", "Colossians": "Col",
    "1 Thessalonians": "1Thess", "2 Thessalonians": "2Thess", "1 Timothy": "1Tim",
    "2 Timothy": "2Tim", "Titus": "Titus", "Philemon": "Phlm", "Hebrews": "Heb", "James": "Jas",
    "1 Peter": "1Pet", "2 Peter": "2Pet", "1 John": "1John", "2 John": "2John",
    "3 John": "3John", "Jude": "Jude", "Revelation": "Rev"
}

# -----------------------------
# SCHEMA
# -----------------------------

DDL = [
# books
"""
CREATE TABLE IF NOT EXISTS books (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_name TEXT NOT NULL UNIQUE,
  osis TEXT,
  index_number INTEGER
);
""",
# chapters
"""
CREATE TABLE IF NOT EXISTS chapters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id INTEGER NOT NULL,
  chapter_number INTEGER NOT NULL,
  UNIQUE(book_id, chapter_number),
  FOREIGN KEY(book_id) REFERENCES books(id)
);
""",
# verses
"""
CREATE TABLE IF NOT EXISTS verses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id INTEGER NOT NULL,
  chapter_id INTEGER NOT NULL,
  verse_num INTEGER NOT NULL,
  ref TEXT,
  text_plain TEXT,
  verse_html TEXT,
  UNIQUE(chapter_id, verse_num),
  FOREIGN KEY(book_id) REFERENCES books(id),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);
""",
# tokens
"""
CREATE TABLE IF NOT EXISTS tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  verse_id INTEGER NOT NULL,
  token_idx INTEGER NOT NULL,         -- reindexed by (vhtml_start, original_idx)
  original_token_idx INTEGER NOT NULL,-- original position in JSON array
  text TEXT NOT NULL,
  strong_norm TEXT,
  strong_raw TEXT,
  morph_norm TEXT,
  morph_raw TEXT,
  morph_gloss TEXT,
  morph_features TEXT,                -- JSON string if present
  italics INTEGER NOT NULL DEFAULT 0,
  html_start INTEGER,
  html_end INTEGER,
  vhtml_start INTEGER,
  vhtml_end INTEGER,
  text_start INTEGER,                 -- NEW: offsets into text_plain
  text_end INTEGER,                   -- NEW: offsets into text_plain
  UNIQUE(verse_id, token_idx),
  FOREIGN KEY(verse_id) REFERENCES verses(id)
);
""",
# footnotes
"""
CREATE TABLE IF NOT EXISTS footnotes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  verse_id INTEGER NOT NULL,
  marker TEXT,
  notetype TEXT,
  ref_attr TEXT,
  xref_attr TEXT,
  body_text TEXT,
  body_html TEXT,
  FOREIGN KEY(verse_id) REFERENCES verses(id)
);
""",
# overrides (optional NER feature)
"""
CREATE TABLE IF NOT EXISTS entity_overrides (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book TEXT NOT NULL,
  chapter INTEGER NOT NULL,
  verse INTEGER NOT NULL,
  start_char INTEGER NOT NULL,
  end_char INTEGER NOT NULL,
  tag TEXT NOT NULL,
  note TEXT
);
""",
# NEW: normalized Strong's lexicon
"""
CREATE TABLE IF NOT EXISTS strongs_lexicon (
  strong_norm TEXT PRIMARY KEY,            -- H#### / G####
  lemma TEXT,
  transliteration TEXT,
  pronunciation TEXT,
  pos TEXT,
  definition TEXT,
  kjv_translation_count TEXT,              -- original raw string (posterity)
  kjv_counts_json TEXT,                    -- parsed structured counts (JSON array)
  etymology TEXT,
  outline_json TEXT                        -- JSON array
);
""",
# indexes
"CREATE INDEX IF NOT EXISTS ix_books_name ON books(book_name);",
"CREATE INDEX IF NOT EXISTS ix_chapters_book ON chapters(book_id, chapter_number);",
"CREATE INDEX IF NOT EXISTS ix_verses_bookchap ON verses(book_id, chapter_id, verse_num);",
"CREATE INDEX IF NOT EXISTS ix_tokens_strong ON tokens(strong_norm);",
"CREATE INDEX IF NOT EXISTS ix_tokens_verse ON tokens(verse_id, token_idx);",
"CREATE INDEX IF NOT EXISTS ix_tokens_verse_offsets ON tokens(verse_id, vhtml_start);",
"CREATE INDEX IF NOT EXISTS ix_lexicon_key ON strongs_lexicon(strong_norm);",
"CREATE INDEX IF NOT EXISTS ix_tokens_verse_textspan ON tokens(verse_id, text_start);",
# views
"""
CREATE VIEW IF NOT EXISTS tokens_visible AS
SELECT *
FROM tokens
WHERE TRIM(COALESCE(text, '')) <> '';
""",
"""
CREATE VIEW IF NOT EXISTS tokens_with_lexicon AS
SELECT t.*, L.lemma, L.transliteration, L.pronunciation, L.pos, L.definition,
       L.kjv_translation_count, L.kjv_counts_json, L.etymology, L.outline_json
FROM tokens t
LEFT JOIN strongs_lexicon L ON L.strong_norm = t.strong_norm;
"""
]


# Optional FTS DDL (built after inserts)
FTS_DDL = [
"""
CREATE VIRTUAL TABLE IF NOT EXISTS verses_fts USING fts5(
  book, chapter, verse, text, content=''
);
"""
]

# -----------------------------
# DB HELPERS
# -----------------------------

def open_db(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    for ddl in DDL:
        con.execute(ddl)
    return con

def create_fts(con: sqlite3.Connection):
    for ddl in FTS_DDL:
        con.execute(ddl)
    # populate FTS once
    con.execute("DELETE FROM verses_fts;")
    con.execute("""
        INSERT INTO verses_fts(book, chapter, verse, text)
        SELECT b.book_name, c.chapter_number, v.verse_num, v.text_plain
        FROM verses v
        JOIN books b   ON v.book_id = b.id
        JOIN chapters c ON v.chapter_id = c.id
    """)

def upsert_book(con: sqlite3.Connection, name: str) -> int:
    osis = OSIS.get(name, name)
    idx = BOOK_INDEX.get(name)
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO books(book_name, osis, index_number) VALUES (?,?,?)", (name, osis, idx))
    cur.execute("SELECT id FROM books WHERE book_name = ?", (name,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO books(book_name, osis, index_number) VALUES (?,?,?)", (name, osis, idx))
        cur.execute("SELECT id FROM books WHERE book_name = ?", (name,))
        row = cur.fetchone()
    return row[0]

def upsert_chapter(con: sqlite3.Connection, book_id: int, ch: int) -> int:
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO chapters(book_id, chapter_number) VALUES (?,?)", (book_id, ch))
    cur.execute("SELECT id FROM chapters WHERE book_id=? AND chapter_number=?", (book_id, ch))
    return cur.fetchone()[0]

def insert_verse(con: sqlite3.Connection, book_id: int, chapter_id: int, verse_obj: Dict[str,Any]) -> int:
    ref = verse_obj.get("ref")
    verse_num = int(verse_obj.get("verse_num") or verse_obj.get("verse") or 0)
    text_plain = verse_obj.get("text_plain")
    verse_html = verse_obj.get("verse_html")
    cur = con.cursor()
    cur.execute("""
      INSERT INTO verses(book_id, chapter_id, verse_num, ref, text_plain, verse_html)
      VALUES(?,?,?,?,?,?)
    """, (book_id, chapter_id, verse_num, ref, text_plain, verse_html))
    return cur.lastrowid

def _order_tokens_for_insert(tokens: List[Dict[str,Any]]) -> List[Tuple[int, Dict[str,Any]]]:
    """
    Returns list of (new_token_idx, token_dict) ordered by:
      1) vhtml_start (None treated as very large)
      2) original index (stable tie-breaker)
    """
    BIG = 10**12
    indexed = [(i, t) for i, t in enumerate(tokens)]
    indexed.sort(key=lambda it: ((it[1].get("vhtml_start") if it[1].get("vhtml_start") is not None else BIG),
                                 it[0]))
    return [(new_i, t) for new_i, (_, t) in enumerate(indexed)]

def insert_tokens(con: sqlite3.Connection, verse_id: int, tokens: List[Dict[str,Any]], strongs_collector: Optional[dict] = None) -> None:
    if not tokens:
        return
    ordered = _order_tokens_for_insert(tokens)
    rows = []
    for new_idx, t in ordered:
        # collect strongs for lexicon table
        if strongs_collector is not None:
            _collect_strongs_from_tokens(strongs_collector, [t])

        rows.append((
            verse_id, new_idx,
            t.get("_original_idx", 0),
            t.get("text"),
            t.get("strong_norm"), t.get("strong_raw"),
            t.get("morph_norm"), t.get("morph_raw"),
            t.get("morph_gloss"),
            json.dumps(t.get("morph_features")) if t.get("morph_features") is not None else None,
            1 if t.get("italics") else 0,
            t.get("html_start"), t.get("html_end"),
            t.get("vhtml_start"), t.get("vhtml_end"),
            t.get("text_start"), t.get("text_end"),
        ))
    con.executemany("""
      INSERT INTO tokens(verse_id, token_idx, original_token_idx, text, strong_norm, strong_raw,
                         morph_norm, morph_raw, morph_gloss, morph_features, italics,
                         html_start, html_end, vhtml_start, vhtml_end, text_start, text_end)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)


def insert_footnotes(con: sqlite3.Connection, verse_id: int, footnotes: List[Dict[str,Any]]) -> None:
    if not footnotes:
        return
    rows = []
    for f in footnotes:
        rows.append((
            verse_id,
            f.get("marker"), f.get("notetype"), f.get("ref_attr"), f.get("xref_attr"),
            f.get("body_text"), f.get("body_html"),
        ))
    con.executemany("""
      INSERT INTO footnotes(verse_id, marker, notetype, ref_attr, xref_attr, body_text, body_html)
      VALUES(?,?,?,?,?,?,?)
    """, rows)

# --- Strong's collection and bulk upsert (from enriched JSON tokens) ---

def _collect_strongs_from_tokens(collector: dict, tokens: List[Dict[str, Any]]):
    """
    Collect Strong's lexicon fields from token dicts (already enriched by exporter).
    collector: dict[str, dict] keyed by strong_norm
    """
    for t in tokens or []:
        s = t.get("strong_norm")
        if not s:
            continue
        # only record if lexicon fields exist (keeps table clean)
        if not any(k in t for k in ("lemma","transliteration","pronunciation","pos","definition",
                                    "kjv_translation_count","kjv_counts","etymology","outline")):
            continue
        entry = collector.get(s) or {}
        # Never overwrite with None; prefer first non-empty seen
        def set_if(d, key, val):
            if val is None:
                return
            if key not in d or d[key] in (None, ""):
                d[key] = val

        set_if(entry, "lemma", t.get("lemma"))
        set_if(entry, "transliteration", t.get("transliteration"))
        set_if(entry, "pronunciation", t.get("pronunciation"))
        set_if(entry, "pos", t.get("pos"))
        set_if(entry, "definition", t.get("definition"))
        set_if(entry, "kjv_translation_count", t.get("kjv_translation_count"))
        # kjv_counts is a list[ {gloss, count} ]; store JSON in DB
        if t.get("kjv_counts") is not None and "kjv_counts_json" not in entry:
            try:
                entry["kjv_counts_json"] = json.dumps(t.get("kjv_counts"), ensure_ascii=False)
            except Exception:
                pass
        set_if(entry, "etymology", t.get("etymology"))
        # outline is a list of strings; store JSON
        if t.get("outline") is not None and "outline_json" not in entry:
            try:
                entry["outline_json"] = json.dumps(t.get("outline"), ensure_ascii=False)
            except Exception:
                pass

        collector[s] = entry

def upsert_strongs_lexicon(con: sqlite3.Connection, collector: dict):
    """
    INSERT OR IGNORE, then UPDATE missing fields (so later chapters can fill gaps).
    """
    if not collector:
        return
    rows = []
    for strong_norm, meta in collector.items():
        rows.append((
            strong_norm,
            meta.get("lemma"), meta.get("transliteration"), meta.get("pronunciation"),
            meta.get("pos"), meta.get("definition"),
            meta.get("kjv_translation_count"), meta.get("kjv_counts_json"),
            meta.get("etymology"), meta.get("outline_json")
        ))
    con.executemany("""
        INSERT OR IGNORE INTO strongs_lexicon(
            strong_norm, lemma, transliteration, pronunciation, pos, definition,
            kjv_translation_count, kjv_counts_json, etymology, outline_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?)
    """, rows)

    # update pass to fill in any missing fields for already-present keys
    con.executemany("""
        UPDATE strongs_lexicon
        SET lemma = COALESCE(lemma, ?),
            transliteration = COALESCE(transliteration, ?),
            pronunciation = COALESCE(pronunciation, ?),
            pos = COALESCE(pos, ?),
            definition = COALESCE(definition, ?),
            kjv_translation_count = COALESCE(kjv_translation_count, ?),
            kjv_counts_json = COALESCE(kjv_counts_json, ?),
            etymology = COALESCE(etymology, ?),
            outline_json = COALESCE(outline_json, ?)
        WHERE strong_norm = ?
    """, [
        (m.get("lemma"), m.get("transliteration"), m.get("pronunciation"),
         m.get("pos"), m.get("definition"),
         m.get("kjv_translation_count"), m.get("kjv_counts_json"),
         m.get("etymology"), m.get("outline_json"),
         k)
        for k, m in collector.items()
    ])


# -----------------------------
# FILE DISCOVERY (ORDER-PRESERVING)
# -----------------------------

_CHAPTER_REGEX = re.compile(r"\.(\d+)\.json$", re.IGNORECASE)

def _book_dir_candidates(root: Path, book_name: str) -> List[Path]:
    candidates = []
    name_spaces = book_name
    name_unders = book_name.replace(" ", "_")

    preferred = [
        f"STEP_{name_unders}",
        f"STEP_{name_spaces}",
        name_unders,
        name_spaces,
    ]
    lower_map = {p.name.lower(): p for p in root.iterdir() if p.is_dir()}
    for cand in preferred:
        p = lower_map.get(cand.lower())
        if p:
            candidates.append(p)

    if not candidates:
        for p in root.iterdir():
            if not p.is_dir():
                continue
            if any(_CHAPTER_REGEX.search(f.name) for f in p.glob("*.json")):
                candidates.append(p)
    return candidates

def _collect_chapter_files(book_dir: Path) -> List[Path]:
    files = [f for f in book_dir.glob("*.json") if f.is_file()]
    pairs: List[Tuple[int, Path]] = []
    for f in files:
        m = _CHAPTER_REGEX.search(f.name)
        if not m:
            continue
        ch = int(m.group(1))
        pairs.append((ch, f))
    pairs.sort(key=lambda x: x[0])
    return [p for _, p in pairs]

def _load_chapter_json(chapter_path: Path) -> Dict[str,Any]:
    return json.loads(chapter_path.read_text(encoding="utf-8"))

# -----------------------------
# MAIN LOAD (STRICT BIBLICAL ORDER)
# -----------------------------

def main():
    if not INPUT_ROOT.exists():
        print(f"❌ Input root not found: {INPUT_ROOT}")
        return

    con = open_db(DB_PATH)
    total_books = total_chapters = total_verses = total_tokens = total_notes = 0
    missing_books: List[str] = []
    strongs_collector: dict = {}  


    try:
        # canonical order
        books_in_order = sorted(BOOK_INDEX.keys(), key=lambda b: BOOK_INDEX[b])

        for book_name in books_in_order:
            candidates = _book_dir_candidates(INPUT_ROOT, book_name)
            if not candidates:
                print(f"⚠️  No folder found for book: {book_name}")
                missing_books.append(book_name)
                continue

            book_dir: Optional[Path] = None
            chapters: List[Path] = []
            for cand in candidates:
                chapters = _collect_chapter_files(cand)
                if chapters:
                    book_dir = cand
                    break

            if not book_dir or not chapters:
                print(f"⚠️  No chapters found for book: {book_name} (checked {', '.join([c.name for c in candidates]) or 'no dirs'})")
                missing_books.append(book_name)
                continue

            print(f"\n📖 Loading {book_name}  [{book_dir}]")
            book_id = upsert_book(con, book_name)
            total_books += 1

            for chap_file in chapters:
                m = _CHAPTER_REGEX.search(chap_file.name)
                chapter_num = int(m.group(1)) if m else None
                if not chapter_num:
                    continue

                chapter_id = upsert_chapter(con, book_id, chapter_num)
                total_chapters += 1

                data = _load_chapter_json(chap_file)
                verses = data.get("verses") if isinstance(data, dict) else data
                if not isinstance(verses, list):
                    print(f"  ⚠️  Unexpected JSON shape in {chap_file.name}; skipping.")
                    continue

                # add original index markers so we can preserve them
                for v in verses:
                    toks = v.get("tokens") or []
                    for i, t in enumerate(toks):
                        # store original JSON index for audit/backtracking
                        t["_original_idx"] = i

                with con:
                    for verse in verses:
                        verse_id = insert_verse(con, book_id, chapter_id, verse)
                        toks = verse.get("tokens") or []
                        fns  = verse.get("footnotes") or []
                        insert_tokens(con, verse_id, toks, strongs_collector)   # pass collector
                        insert_footnotes(con, verse_id, fns)
                        total_verses += 1
                        total_tokens += len(toks)
                        total_notes  += len(fns)

                print(f"  ✓ Chapter {chapter_num:>3} — verses: {len(verses)}")

        # Upsert Strong's lexicon collected from tokens
        try:
            with con:
                upsert_strongs_lexicon(con, strongs_collector)
            print(f"\n📚 Strong's lexicon entries loaded: {len(strongs_collector)}")
        except sqlite3.Error as e:
            print(f"\n⚠️  Could not upsert strongs_lexicon: {e}")


        # Optional FTS
        if CREATE_VERSES_FTS:
            try:
                create_fts(con)
                print("\n🔎 FTS built: verses_fts")
            except sqlite3.Error as e:
                print(f"\n⚠️  Could not create FTS: {e}. You can set CREATE_VERSES_FTS=False.")

        # Summary
        print("\n==================== SUMMARY ====================")
        print(f"  Books loaded:    {total_books} (out of {len(BOOK_INDEX)})")
        print(f"  Chapters loaded: {total_chapters}")
        print(f"  Verses loaded:   {total_verses}")
        print(f"  Tokens loaded:   {total_tokens}")
        print(f"  Footnotes:       {total_notes}")
        print(f"  DB path:         {Path(DB_PATH).resolve()}")
        if missing_books:
            print("\n  Missing/empty books (not found in input root):")
            for b in missing_books:
                print(f"   - {b}")

    finally:
        try:
            con.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
