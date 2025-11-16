#!/usr/bin/env python3
"""Find missing verses in GoodBook.db compared to canonical verse counts"""
import sqlite3
import sys
sys.path.insert(0, r"D:\Project_PP\projects\bible\code\STEP")
from step_constants import BOOK_CHAPTERS

# Expected verse counts for each chapter (Protestant Bible - ESV/KJV standard)
# This is the canonical verse count
VERSE_COUNTS = {
    # Old Testament
    ("Genesis", 1): 31, ("Genesis", 2): 25, ("Genesis", 3): 24, ("Genesis", 4): 26, ("Genesis", 5): 32,
    ("Genesis", 6): 22, ("Genesis", 7): 24, ("Genesis", 8): 22, ("Genesis", 9): 29, ("Genesis", 10): 32,
    # ... (this would need all verse counts for all chapters)
    # For now, let's just query the database for gaps in verse numbering
}

DB_PATH = r"D:\Project_PP\projects\bible\data\GoodBook.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get all books in order
cur.execute("""
    SELECT DISTINCT b.id, b.book_name
    FROM books b
    ORDER BY b.id
""")
books = cur.fetchall()

print("Checking for missing verses (gaps in verse numbering)...")
print("=" * 80)

missing_verses = []

for book_id, book_name in books:
    # Get all chapters for this book
    cur.execute("""
        SELECT c.id, c.chapter_number
        FROM chapters c
        WHERE c.book_id = ?
        ORDER BY c.chapter_number
    """, (book_id,))
    chapters = cur.fetchall()

    for chapter_id, chapter_num in chapters:
        # Get all verse numbers for this chapter
        cur.execute("""
            SELECT verse_number
            FROM verses
            WHERE chapter_id = ?
            ORDER BY verse_number
        """, (chapter_id,))
        verses = [row[0] for row in cur.fetchall()]

        if not verses:
            continue

        # Check for gaps in verse numbering (1, 2, 3, ... max_verse)
        max_verse = max(verses)
        expected_verses = set(range(1, max_verse + 1))
        actual_verses = set(verses)
        missing_in_chapter = expected_verses - actual_verses

        if missing_in_chapter:
            for verse_num in sorted(missing_in_chapter):
                missing_verses.append((book_name, chapter_num, verse_num))
                print(f"Missing: {book_name} {chapter_num}:{verse_num}")

conn.close()

print("=" * 80)
print(f"Total missing verses with gaps: {len(missing_verses)}")

if len(missing_verses) == 4:
    print("\n✓ Found the 4 missing verses!")
else:
    print(f"\nNote: Found {len(missing_verses)} gaps, expected 4")
    print("Some missing verses may not be gaps but truly don't exist in the source.")
