#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import text from STEP JSON files into GoodBook.db

This script:
- Reads JSON files from cache folders (e.g., cache/Genesis/STEP_Genesis.1.json)
- Adds text_esv column to verses table if it doesn't exist
- Inserts STEP text into the text_esv column
- Matches by Book, Chapter, and Verse

Usage:
    python import_STEP_goodbook.py
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List

# ============================================================================
# Configuration
# ============================================================================

DB_PATH = r"D:\Project_PP\projects\bible\data\GoodBook.db"
CACHE_ROOT = Path(r"D:\Project_PP\projects\bible\cache")

# Book canonical order and OSIS codes
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

BOOK_OSIS: Dict[str, str] = {
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


# ============================================================================
# Database Setup
# ============================================================================

def create_schema(conn: sqlite3.Connection):
    """Create books and chapters tables if they don't exist.

    Also adds text_esv column to verses table if it doesn't exist.
    """
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_name TEXT NOT NULL UNIQUE,
            osis TEXT,
            book_index INTEGER
        );

        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            chapter_number INTEGER NOT NULL,
            UNIQUE(book_id, chapter_number),
            FOREIGN KEY(book_id) REFERENCES books(id)
        );

        CREATE INDEX IF NOT EXISTS ix_books_name ON books(book_name);
        CREATE INDEX IF NOT EXISTS ix_chapters_book ON chapters(book_id, chapter_number);
        CREATE INDEX IF NOT EXISTS ix_verses_chapter ON verses(chapter_id, verse_number);
    """)

    # Add text_esv column to verses table if it doesn't exist
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(verses)")
    columns = [row[1] for row in cur.fetchall()]

    if 'text_esv' not in columns:
        print("Adding text_esv column to verses table...")
        cur.execute("ALTER TABLE verses ADD COLUMN text_esv TEXT")
        conn.commit()


# ============================================================================
# Database Helpers
# ============================================================================

def get_or_create_book(conn: sqlite3.Connection, book_name: str) -> int:
    """Get or create book, return book_id."""
    osis = BOOK_OSIS.get(book_name, book_name)
    book_index = BOOK_INDEX.get(book_name)

    cur = conn.cursor()
    cur.execute("SELECT id FROM books WHERE book_name = ?", (book_name,))
    row = cur.fetchone()

    if row:
        return row[0]

    cur.execute(
        "INSERT INTO books (book_name, osis, book_index) VALUES (?, ?, ?)",
        (book_name, osis, book_index)
    )
    if cur.lastrowid is None:
        raise RuntimeError(f"Failed to insert book: {book_name}")
    return cur.lastrowid


def get_or_create_chapter(conn: sqlite3.Connection, book_id: int, chapter_num: int) -> int:
    """Get or create chapter, return chapter_id."""
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM chapters WHERE book_id = ? AND chapter_number = ?",
        (book_id, chapter_num)
    )
    row = cur.fetchone()

    if row:
        return row[0]

    cur.execute(
        "INSERT INTO chapters (book_id, chapter_number) VALUES (?, ?)",
        (book_id, chapter_num)
    )
    if cur.lastrowid is None:
        raise RuntimeError(f"Failed to insert chapter: {chapter_num} for book_id: {book_id}")
    return cur.lastrowid


def insert_or_update_verse(
    conn: sqlite3.Connection,
    chapter_id: int,
    verse_num: int,
    text_esv: str
):
    """Update verse text_esv in GoodBook.db (only updates existing verses)."""
    cur = conn.cursor()

    # Check if verse exists
    cur.execute(
        "SELECT id FROM verses WHERE chapter_id = ? AND verse_number = ?",
        (chapter_id, verse_num)
    )
    row = cur.fetchone()

    if row:
        # Update existing verse with STEP/ESV text
        cur.execute(
            "UPDATE verses SET text_esv = ? WHERE id = ?",
            (text_esv, row[0])
        )
    # else: Skip verses that don't exist in the database


# ============================================================================
# File Discovery
# ============================================================================

def find_chapter_files(book_dir: Path) -> List[Path]:
    """Find all chapter JSON files in a book directory, sorted by chapter number."""
    import re

    files = list(book_dir.glob("*.json"))
    chapter_pattern = re.compile(r"\.(\d+)\.json$", re.IGNORECASE)

    chapters = []
    for f in files:
        match = chapter_pattern.search(f.name)
        if match:
            ch_num = int(match.group(1))
            chapters.append((ch_num, f))

    chapters.sort(key=lambda x: x[0])
    return [f for _, f in chapters]


# ============================================================================
# Main Import
# ============================================================================

def main():
    """Import text_plain from STEP JSON files into GoodBook.db."""

    if not CACHE_ROOT.exists():
        print(f"ERROR: Cache directory not found: {CACHE_ROOT}")
        return

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Create schema
    create_schema(conn)

    # Track progress
    total_books = 0
    total_chapters = 0
    total_verses = 0
    missing_books = []

    print(f"Importing text from {CACHE_ROOT} into {DB_PATH}")
    print("=" * 60)

    # Process books in canonical order
    books_in_order = sorted(BOOK_INDEX.keys(), key=lambda b: BOOK_INDEX[b])

    for book_name in books_in_order:
        # Find book directory
        book_dir = CACHE_ROOT / book_name
        if not book_dir.exists() or not book_dir.is_dir():
            missing_books.append(book_name)
            continue

        # Find chapter files
        chapter_files = find_chapter_files(book_dir)
        if not chapter_files:
            missing_books.append(book_name)
            continue

        print(f"\n[{book_name}] ({len(chapter_files)} chapters)")

        # Get or create book
        book_id = get_or_create_book(conn, book_name)
        total_books += 1

        # Process each chapter
        for chapter_file in chapter_files:
            # Extract chapter number from filename
            import re
            match = re.search(r"\.(\d+)\.json$", chapter_file.name)
            if not match:
                continue
            chapter_num = int(match.group(1))

            # Load JSON
            data = json.loads(chapter_file.read_text(encoding="utf-8"))
            verses = data.get("verses", [])

            if not verses:
                print(f"  WARNING: No verses in chapter {chapter_num}")
                continue

            # Get or create chapter
            chapter_id = get_or_create_chapter(conn, book_id, chapter_num)
            total_chapters += 1

            # Insert verses
            for verse_obj in verses:
                verse_num = verse_obj.get("verse_num") or verse_obj.get("verse")
                if verse_num is None:
                    continue

                text_esv = verse_obj.get("text_plain", "")

                insert_or_update_verse(
                    conn, chapter_id, int(verse_num), text_esv
                )
                total_verses += 1

            conn.commit()
            print(f"  OK Chapter {chapter_num:3d} - {len(verses)} verses")

    # Close database
    conn.close()

    # Print summary
    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)
    print(f"Books imported:    {total_books}/{len(BOOK_INDEX)}")
    print(f"Chapters imported: {total_chapters}")
    print(f"Verses imported:   {total_verses}")
    print(f"Database:          {Path(DB_PATH).resolve()}")

    if missing_books:
        print(f"\nMissing books ({len(missing_books)}):")
        for book in missing_books:
            print(f"  - {book}")


if __name__ == "__main__":
    main()
