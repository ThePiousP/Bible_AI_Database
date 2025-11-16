#!/usr/bin/env python3
"""
Diagnostic: Check ESV vs KJV text in database
"""

import sqlite3

DB_PATH = r"D:\Project_PP\projects\Bible\data\GoodBook.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get first 5 verses to compare
cursor.execute("""
    SELECT v.verse_number, v.text, v.text_esv, c.chapter_number, b.book_name
    FROM verses v
    LEFT JOIN chapters c ON v.chapter_id = c.id
    LEFT JOIN books b ON c.book_id = b.id
    LIMIT 5
""")

rows = cursor.fetchall()

for idx, row in enumerate(rows):
    verse_num, text_kjv, text_esv, chapter, book = row
    print(f"\n{'='*70}")
    print(f"Verse {idx+1}: {book} {chapter}:{verse_num}")
    print(f"{'='*70}")
    print(f"KJV text:\n  {text_kjv[:100]}...")
    print(f"\nESV text:\n  {text_esv[:100] if text_esv else 'NULL or EMPTY'}...")
    print(f"\nESV is NULL? {text_esv is None}")
    print(f"ESV is empty? {text_esv == '' if text_esv else 'N/A'}")

conn.close()
