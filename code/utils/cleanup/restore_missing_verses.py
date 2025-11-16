#!/usr/bin/env python3
"""Restore the 4 missing verses from cache files"""
import json
import sqlite3
from pathlib import Path

DB_PATH = r"D:\Project_PP\projects\bible\data\GoodBook.db"
CACHE_ROOT = Path(r"D:\Project_PP\projects\bible\cache")

# The 4 missing verses
MISSING = [
    ("Psalms", 47, 1),
    ("Isaiah", 12, 1),
    ("Malachi", 4, 2),
    ("Acts", 11, 4)
]

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")

print("Restoring 4 missing verses...")
print("=" * 60)

restored = 0

for book_name, chapter_num, verse_num in MISSING:
    # Load cache file
    cache_file = CACHE_ROOT / book_name / f"STEP_{book_name}.{chapter_num}.json"

    if not cache_file.exists():
        print(f"ERROR: Cache file not found: {cache_file}")
        continue

    data = json.loads(cache_file.read_text(encoding="utf-8"))

    # Find the specific verse
    verse_data = None
    for v in data["verses"]:
        if v.get("verse_num") == verse_num or v.get("verse") == verse_num:
            verse_data = v
            break

    if not verse_data:
        print(f"ERROR: Verse {book_name} {chapter_num}:{verse_num} not found in cache")
        continue

    # Get book_id
    cur = conn.cursor()
    cur.execute("SELECT id FROM books WHERE book_name = ?", (book_name,))
    book_row = cur.fetchone()
    if not book_row:
        print(f"ERROR: Book '{book_name}' not found in database")
        continue
    book_id = book_row[0]

    # Get chapter_id
    cur.execute("SELECT id FROM chapters WHERE book_id = ? AND chapter_number = ?", (book_id, chapter_num))
    chapter_row = cur.fetchone()
    if not chapter_row:
        print(f"ERROR: Chapter {book_name} {chapter_num} not found in database")
        continue
    chapter_id = chapter_row[0]

    # Extract text
    text = verse_data.get("text_plain", "")
    text_esv = verse_data.get("text_plain", "")  # Using same text for both

    # Insert the verse
    cur.execute("""
        INSERT INTO verses (chapter_id, verse_number, text, text_esv)
        VALUES (?, ?, ?, ?)
    """, (chapter_id, verse_num, text, text_esv))

    conn.commit()
    restored += 1
    print(f"OK Restored: {book_name} {chapter_num}:{verse_num}")

conn.close()

print("=" * 60)
print(f"Restored {restored} verses")
print(f"\nFinal count should now be 31,102!")
