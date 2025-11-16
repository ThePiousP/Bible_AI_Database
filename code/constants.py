#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
constants.py
Centralized constants for the Bible NER pipeline

This module contains all canonical constants used throughout the project.
Previously, these were scattered across multiple files as magic numbers.

Changes from old code:
  - BEFORE: Hardcoded "150" for Psalms chapters in step_adapter.py
  - AFTER: BOOK_CHAPTERS["Psalms"] (validated, documented)

  - BEFORE: Hardcoded "66" for book count
  - AFTER: NUM_CANONICAL_BOOKS constant

  - BEFORE: Alignment window "200" in export_ner_silver.py:529
  - AFTER: ALIGNMENT_FALLBACK_WINDOW constant

Created: 2025-10-29 (Phase 1 Refactoring)
"""

from typing import Final, Dict

# ============================================================================
# Bible Structure Constants
# ============================================================================

NUM_CANONICAL_BOOKS: Final = 66
NUM_OLD_TESTAMENT_BOOKS: Final = 39
NUM_NEW_TESTAMENT_BOOKS: Final = 27

# Expected verse/chapter counts (for validation)
EXPECTED_TOTAL_VERSES: Final = 31102  # KJV/NKJV standard
EXPECTED_TOTAL_CHAPTERS: Final = 1189

# ============================================================================
# Book Chapter Counts (Canonical Order)
# ============================================================================
# Previously scattered across step_adapter.py and bible_scraper.py

OLD_TESTAMENT_BOOKS: Final[Dict[str, int]] = {
    "Genesis": 50,
    "Exodus": 40,
    "Leviticus": 27,
    "Numbers": 36,
    "Deuteronomy": 34,
    "Joshua": 24,
    "Judges": 21,
    "Ruth": 4,
    "1 Samuel": 31,
    "2 Samuel": 24,
    "1 Kings": 22,
    "2 Kings": 25,
    "1 Chronicles": 29,
    "2 Chronicles": 36,
    "Ezra": 10,
    "Nehemiah": 13,
    "Esther": 10,
    "Job": 42,
    "Psalms": 150,  # ← BEFORE: Hardcoded 150 in step_adapter.py:39
    "Proverbs": 31,
    "Ecclesiastes": 12,
    "Song of Solomon": 8,
    "Isaiah": 66,
    "Jeremiah": 52,
    "Lamentations": 5,
    "Ezekiel": 48,
    "Daniel": 12,
    "Hosea": 14,
    "Joel": 3,
    "Amos": 9,
    "Obadiah": 1,
    "Jonah": 4,
    "Micah": 7,
    "Nahum": 3,
    "Habakkuk": 3,
    "Zephaniah": 3,
    "Haggai": 2,
    "Zechariah": 14,
    "Malachi": 4,
}

NEW_TESTAMENT_BOOKS: Final[Dict[str, int]] = {
    "Matthew": 28,
    "Mark": 16,
    "Luke": 24,
    "John": 21,
    "Acts": 28,
    "Romans": 16,
    "1 Corinthians": 16,
    "2 Corinthians": 13,
    "Galatians": 6,
    "Ephesians": 6,
    "Philippians": 4,
    "Colossians": 4,
    "1 Thessalonians": 5,
    "2 Thessalonians": 3,
    "1 Timothy": 6,
    "2 Timothy": 4,
    "Titus": 3,
    "Philemon": 1,
    "Hebrews": 13,
    "James": 5,
    "1 Peter": 5,
    "2 Peter": 3,
    "1 John": 5,
    "2 John": 1,
    "3 John": 1,
    "Jude": 1,
    "Revelation": 22,
}

# Combined dictionary (all 66 books)
BOOK_CHAPTERS: Final[Dict[str, int]] = {
    **OLD_TESTAMENT_BOOKS,
    **NEW_TESTAMENT_BOOKS
}

# Validate at import time
assert len(BOOK_CHAPTERS) == NUM_CANONICAL_BOOKS, \
    f"Expected {NUM_CANONICAL_BOOKS} books, got {len(BOOK_CHAPTERS)}"
assert sum(BOOK_CHAPTERS.values()) == EXPECTED_TOTAL_CHAPTERS, \
    f"Expected {EXPECTED_TOTAL_CHAPTERS} chapters, got {sum(BOOK_CHAPTERS.values())}"

# ============================================================================
# Book Canonical Order (1-66)
# ============================================================================
# Previously hardcoded in step_adapter.py:55-70

BOOK_INDEX: Final[Dict[str, int]] = {
    # Old Testament (1-39)
    "Genesis": 1, "Exodus": 2, "Leviticus": 3, "Numbers": 4, "Deuteronomy": 5,
    "Joshua": 6, "Judges": 7, "Ruth": 8, "1 Samuel": 9, "2 Samuel": 10,
    "1 Kings": 11, "2 Kings": 12, "1 Chronicles": 13, "2 Chronicles": 14,
    "Ezra": 15, "Nehemiah": 16, "Esther": 17, "Job": 18, "Psalms": 19,
    "Proverbs": 20, "Ecclesiastes": 21, "Song of Solomon": 22, "Isaiah": 23,
    "Jeremiah": 24, "Lamentations": 25, "Ezekiel": 26, "Daniel": 27, "Hosea": 28,
    "Joel": 29, "Amos": 30, "Obadiah": 31, "Jonah": 32, "Micah": 33, "Nahum": 34,
    "Habakkuk": 35, "Zephaniah": 36, "Haggai": 37, "Zechariah": 38, "Malachi": 39,
    # New Testament (40-66)
    "Matthew": 40, "Mark": 41, "Luke": 42, "John": 43, "Acts": 44, "Romans": 45,
    "1 Corinthians": 46, "2 Corinthians": 47, "Galatians": 48, "Ephesians": 49,
    "Philippians": 50, "Colossians": 51, "1 Thessalonians": 52, "2 Thessalonians": 53,
    "1 Timothy": 54, "2 Timothy": 55, "Titus": 56, "Philemon": 57, "Hebrews": 58,
    "James": 59, "1 Peter": 60, "2 Peter": 61, "1 John": 62, "2 John": 63,
    "3 John": 64, "Jude": 65, "Revelation": 66
}

# Reverse mapping (index → book name)
INDEX_TO_BOOK: Final[Dict[int, str]] = {v: k for k, v in BOOK_INDEX.items()}

# ============================================================================
# OSIS Book Codes (for STEP data)
# ============================================================================
# Previously in step_adapter.py:73-91

BOOK_OSIS: Final[Dict[str, str]] = {
    "Genesis": "Gen", "Exodus": "Exo", "Leviticus": "Lev", "Numbers": "Num",
    "Deuteronomy": "Deut", "Joshua": "Josh", "Judges": "Judg", "Ruth": "Ruth",
    "1 Samuel": "1Sam", "2 Samuel": "2Sam", "1 Kings": "1Kgs", "2 Kings": "2Kgs",
    "1 Chronicles": "1Chr", "2 Chronicles": "2Chr", "Ezra": "Ezra", "Nehemiah": "Neh",
    "Esther": "Est", "Job": "Job", "Psalms": "Psa", "Proverbs": "Prov",
    "Ecclesiastes": "Eccl", "Song of Solomon": "Song", "Isaiah": "Isa",
    "Jeremiah": "Jer", "Lamentations": "Lam", "Ezekiel": "Ezek", "Daniel": "Dan",
    "Hosea": "Hos", "Joel": "Joel", "Amos": "Amos", "Obadiah": "Obad",
    "Jonah": "Jonah", "Micah": "Mic", "Nahum": "Nah", "Habakkuk": "Hab",
    "Zephaniah": "Zeph", "Haggai": "Hag", "Zechariah": "Zech", "Malachi": "Mal",
    "Matthew": "Matt", "Mark": "Mark", "Luke": "Luke", "John": "John", "Acts": "Acts",
    "Romans": "Rom", "1 Corinthians": "1Cor", "2 Corinthians": "2Cor",
    "Galatians": "Gal", "Ephesians": "Eph", "Philippians": "Phil", "Colossians": "Col",
    "1 Thessalonians": "1Thess", "2 Thessalonians": "2Thess", "1 Timothy": "1Tim",
    "2 Timothy": "2Tim", "Titus": "Titus", "Philemon": "Phlm", "Hebrews": "Heb",
    "James": "Jas", "1 Peter": "1Pet", "2 Peter": "2Pet", "1 John": "1John",
    "2 John": "2John", "3 John": "3John", "Jude": "Jude", "Revelation": "Rev"
}

# Reverse mapping (OSIS → book name)
OSIS_TO_BOOK: Final[Dict[str, str]] = {v: k for k, v in BOOK_OSIS.items()}

# ============================================================================
# Alignment Algorithm Constants
# ============================================================================
# Previously hardcoded magic numbers in export_ner_silver.py

ALIGNMENT_FALLBACK_WINDOW: Final = 200
# ↑ BEFORE: Hardcoded 200 in export_ner_silver.py:529
# ↑ AFTER: Named constant with documentation
# Used for: Fallback window size when searching for token with light normalization

ALIGNMENT_WHITESPACE_TOLERANCE: Final = True
# Allow collapsing multiple spaces during alignment

# ============================================================================
# Strong's Concordance Constants
# ============================================================================

STRONGS_HEBREW_MIN: Final = 1
STRONGS_HEBREW_MAX: Final = 8674  # H1-H8674

STRONGS_GREEK_MIN: Final = 1
STRONGS_GREEK_MAX: Final = 5624  # G1-G5624

EXPECTED_STRONGS_ENTRIES: Final = STRONGS_HEBREW_MAX + STRONGS_GREEK_MAX  # ~14,298

# ============================================================================
# Database Constraints
# ============================================================================

MAX_CROSS_REFERENCES_PER_VERSE: Final = 100
# Sanity check - if a verse has >100 cross-refs, likely data error

# ============================================================================
# Silver Export Defaults
# ============================================================================
# Previously in silver_config.yml and export_ner_silver.py

DEFAULT_RANDOM_SEED: Final = 13  # For reproducible splits
DEFAULT_TRAIN_RATIO: Final = 0.8
DEFAULT_DEV_RATIO: Final = 0.1
DEFAULT_TEST_RATIO: Final = 0.1

# ============================================================================
# Entity Label Constants
# ============================================================================
# Number of entity labels defined in label_rules.yml

NUM_ENTITY_LABELS: Final = 65  # As of v0.983

# Core entity categories (for validation)
CORE_ENTITY_TYPES: Final = [
    "DEITY",
    "PERSON",
    "LOCATION",
    "DIVINE_TITLE",
    "PROPHET",
]

# ============================================================================
# Helper Functions
# ============================================================================

def validate_book_name(book_name: str) -> bool:
    """Check if book name is valid canonical name."""
    return book_name in BOOK_CHAPTERS


def get_book_chapter_count(book_name: str) -> int:
    """Get number of chapters for a book."""
    return BOOK_CHAPTERS.get(book_name, 0)


def get_book_index(book_name: str) -> int:
    """Get canonical index (1-66) for a book."""
    return BOOK_INDEX.get(book_name, 0)


def get_osis_code(book_name: str) -> str:
    """Get OSIS code for a book."""
    return BOOK_OSIS.get(book_name, "")


def is_old_testament(book_name: str) -> bool:
    """Check if book is Old Testament."""
    return book_name in OLD_TESTAMENT_BOOKS


def is_new_testament(book_name: str) -> bool:
    """Check if book is New Testament."""
    return book_name in NEW_TESTAMENT_BOOKS


# ============================================================================
# Usage Examples (for documentation)
# ============================================================================

if __name__ == "__main__":
    # Example usage
    print(f"Total canonical books: {NUM_CANONICAL_BOOKS}")
    print(f"Psalms has {BOOK_CHAPTERS['Psalms']} chapters")
    print(f"Genesis is book #{BOOK_INDEX['Genesis']}")
    print(f"Matthew OSIS code: {BOOK_OSIS['Matthew']}")
    print(f"Is Genesis OT? {is_old_testament('Genesis')}")

    # Validate all constants
    assert len(BOOK_INDEX) == NUM_CANONICAL_BOOKS
    assert len(BOOK_OSIS) == NUM_CANONICAL_BOOKS
    assert len(OLD_TESTAMENT_BOOKS) == NUM_OLD_TESTAMENT_BOOKS
    assert len(NEW_TESTAMENT_BOOKS) == NUM_NEW_TESTAMENT_BOOKS

    print("\n✓ All constants validated successfully!")
