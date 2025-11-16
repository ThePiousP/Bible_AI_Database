#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step_constants.py
Biblical canon catalogs, OSIS codes, and book metadata for STEP parsing

BEFORE (Phase 1):
  - Hardcoded dictionaries in step_adapter.py (lines 33-91)
  - Magic numbers: "Psalms": 150, book counts, etc.
  - No validation

AFTER (Phase 2):
  - Centralized in dedicated module
  - Reuses code/constants.py from Phase 1
  - Type hints added
  - Validation functions
  - Backward compatible

Created: 2025-10-29 (Phase 2 Refactoring)
"""

from typing import Dict, Optional, Final
from pathlib import Path
import sys

# Import centralized constants from Phase 1 (if available)
try:
    # Try to import from Phase 1 centralized constants
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from constants import (
        OLD_TESTAMENT_BOOKS as _OT_BOOKS,
        NEW_TESTAMENT_BOOKS as _NT_BOOKS,
        BOOK_CHAPTERS as _BOOK_CHAPTERS,
        BOOK_INDEX as _BOOK_INDEX,
        BOOK_OSIS as _BOOK_OSIS
    )
    _USING_PHASE1_CONSTANTS = True
except ImportError:
    # Fallback to local definitions if Phase 1 not available
    _USING_PHASE1_CONSTANTS = False
    _OT_BOOKS = None
    _NT_BOOKS = None
    _BOOK_CHAPTERS = None
    _BOOK_INDEX = None
    _BOOK_OSIS = None


# ============================================================================
# Biblical Canon - Old Testament
# ============================================================================

OLD_TESTAMENT_BOOKS: Final[Dict[str, int]] = _OT_BOOKS if _USING_PHASE1_CONSTANTS else {
    "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34,
    "Joshua": 24, "Judges": 21, "Ruth": 4, "1 Samuel": 31, "2 Samuel": 24,
    "1 Kings": 22, "2 Kings": 25, "1 Chronicles": 29, "2 Chronicles": 36, "Ezra": 10,
    "Nehemiah": 13, "Esther": 10, "Job": 42, "Psalms": 150, "Proverbs": 31,
    "Ecclesiastes": 12, "Song of Solomon": 8, "Isaiah": 66, "Jeremiah": 52,
    "Lamentations": 5, "Ezekiel": 48, "Daniel": 12, "Hosea": 14, "Joel": 3,
    "Amos": 9, "Obadiah": 1, "Jonah": 4, "Micah": 7, "Nahum": 3, "Habakkuk": 3,
    "Zephaniah": 3, "Haggai": 2, "Zechariah": 14, "Malachi": 4
}


# ============================================================================
# Biblical Canon - New Testament
# ============================================================================

NEW_TESTAMENT_BOOKS: Final[Dict[str, int]] = _NT_BOOKS if _USING_PHASE1_CONSTANTS else {
    "Matthew": 28, "Mark": 16, "Luke": 24, "John": 21, "Acts": 28,
    "Romans": 16, "1 Corinthians": 16, "2 Corinthians": 13, "Galatians": 6,
    "Ephesians": 6, "Philippians": 4, "Colossians": 4, "1 Thessalonians": 5,
    "2 Thessalonians": 3, "1 Timothy": 6, "2 Timothy": 4, "Titus": 3,
    "Philemon": 1, "Hebrews": 13, "James": 5, "1 Peter": 5, "2 Peter": 3,
    "1 John": 5, "2 John": 1, "3 John": 1, "Jude": 1, "Revelation": 22
}


# ============================================================================
# Combined Book Chapters (All 66 Books)
# ============================================================================

BOOK_CHAPTERS: Final[Dict[str, int]] = _BOOK_CHAPTERS if _USING_PHASE1_CONSTANTS else {
    **OLD_TESTAMENT_BOOKS,
    **NEW_TESTAMENT_BOOKS
}


# ============================================================================
# Canonical Book Index (1-66)
# ============================================================================

BOOK_INDEX: Final[Dict[str, int]] = _BOOK_INDEX if _USING_PHASE1_CONSTANTS else {
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


# ============================================================================
# OSIS Codes (for STEP refs and local HTML filenames)
# ============================================================================

BOOK_OSIS: Final[Dict[str, str]] = _BOOK_OSIS if _USING_PHASE1_CONSTANTS else {
    # Old Testament
    "Genesis": "Gen", "Exodus": "Exo", "Leviticus": "Lev", "Numbers": "Num", "Deuteronomy": "Deut",
    "Joshua": "Josh", "Judges": "Judg", "Ruth": "Ruth",
    "1 Samuel": "1Sam", "2 Samuel": "2Sam",
    "1 Kings": "1Kgs", "2 Kings": "2Kgs",
    "1 Chronicles": "1Chr", "2 Chronicles": "2Chr",
    "Ezra": "Ezra", "Nehemiah": "Neh", "Esther": "Est",
    "Job": "Job", "Psalms": "Psa", "Proverbs": "Prov", "Ecclesiastes": "Eccl",
    "Song of Solomon": "Song", "Isaiah": "Isa", "Jeremiah": "Jer", "Lamentations": "Lam",
    "Ezekiel": "Ezek", "Daniel": "Dan", "Hosea": "Hos", "Joel": "Joel", "Amos": "Amos",
    "Obadiah": "Obad", "Jonah": "Jonah", "Micah": "Mic", "Nahum": "Nah", "Habakkuk": "Hab",
    "Zephaniah": "Zeph", "Haggai": "Hag", "Zechariah": "Zech", "Malachi": "Mal",
    # New Testament
    "Matthew": "Matt", "Mark": "Mark", "Luke": "Luke", "John": "John", "Acts": "Acts",
    "Romans": "Rom", "1 Corinthians": "1Cor", "2 Corinthians": "2Cor", "Galatians": "Gal",
    "Ephesians": "Eph", "Philippians": "Phil", "Colossians": "Col", "1 Thessalonians": "1Thess",
    "2 Thessalonians": "2Thess", "1 Timothy": "1Tim", "2 Timothy": "2Tim", "Titus": "Titus",
    "Philemon": "Phlm", "Hebrews": "Heb", "James": "Jas", "1 Peter": "1Pet", "2 Peter": "2Pet",
    "1 John": "1John", "2 John": "2John", "3 John": "3John", "Jude": "Jude", "Revelation": "Rev"
}


# ============================================================================
# Validation & Helper Functions
# ============================================================================

def is_valid_book(book_name: str) -> bool:
    """
    Check if a book name is in the canonical 66-book Bible.

    Args:
        book_name: Full book name (e.g., "Genesis", "1 John")

    Returns:
        True if valid, False otherwise
    """
    return book_name in BOOK_CHAPTERS


def get_chapter_count(book_name: str) -> Optional[int]:
    """
    Get the number of chapters in a book.

    Args:
        book_name: Full book name

    Returns:
        Number of chapters, or None if invalid book

    Example:
        >>> get_chapter_count("Psalms")
        150
        >>> get_chapter_count("Invalid")
        None
    """
    return BOOK_CHAPTERS.get(book_name)


def get_osis_code(book_name: str) -> Optional[str]:
    """
    Get the OSIS code for a book.

    Args:
        book_name: Full book name

    Returns:
        OSIS code (e.g., "Gen", "Matt"), or None if invalid

    Example:
        >>> get_osis_code("Genesis")
        'Gen'
        >>> get_osis_code("Matthew")
        'Matt'
    """
    return BOOK_OSIS.get(book_name)


def get_book_index(book_name: str) -> Optional[int]:
    """
    Get the canonical index (1-66) for a book.

    Args:
        book_name: Full book name

    Returns:
        Index (1-66), or None if invalid

    Example:
        >>> get_book_index("Genesis")
        1
        >>> get_book_index("Revelation")
        66
    """
    return BOOK_INDEX.get(book_name)


def is_old_testament(book_name: str) -> bool:
    """Check if a book is in the Old Testament."""
    return book_name in OLD_TESTAMENT_BOOKS


def is_new_testament(book_name: str) -> bool:
    """Check if a book is in the New Testament."""
    return book_name in NEW_TESTAMENT_BOOKS


def get_all_books_in_order() -> list[str]:
    """
    Get all 66 book names in canonical order.

    Returns:
        List of book names sorted by BOOK_INDEX
    """
    return sorted(BOOK_INDEX.keys(), key=lambda b: BOOK_INDEX[b])


def resolve_book_code(user_input: str) -> Optional[str]:
    """
    Resolve user input to a valid OSIS book code.

    Handles full book names, OSIS codes, and partial matches.
    Special handling for ambiguous cases like "Jud" (Judges vs Jude).

    Args:
        user_input: User's book input (e.g., "Gen", "Genesis", "Jud", "Jude")

    Returns:
        Valid OSIS code, or None if no match found

    Examples:
        >>> resolve_book_code("Gen")
        'Gen'
        >>> resolve_book_code("Genesis")
        'Gen'
        >>> resolve_book_code("Jude")
        'Jude'
        >>> resolve_book_code("Judg")
        'Judg'
        >>> resolve_book_code("Judges")
        'Judg'
    """
    if not user_input:
        return None

    inp = user_input.strip()

    # 1. Try exact OSIS code match (case-insensitive)
    for osis_code in BOOK_OSIS.values():
        if inp.lower() == osis_code.lower():
            return osis_code

    # 2. Try exact book name match (case-insensitive)
    for book_name, osis_code in BOOK_OSIS.items():
        if inp.lower() == book_name.lower():
            return osis_code

    # 3. Handle ambiguous "Jud" case - default to Jude (the shorter book)
    #    User must type "Judg" or "Judges" to get Judges
    if inp.lower() == "jud":
        return "Jude"

    # 4. Try partial OSIS code match (must be unique)
    osis_matches = [code for code in BOOK_OSIS.values() if code.lower().startswith(inp.lower())]
    if len(osis_matches) == 1:
        return osis_matches[0]

    # 5. Try partial book name match (must be unique)
    name_matches = [
        (name, code) for name, code in BOOK_OSIS.items()
        if name.lower().startswith(inp.lower())
    ]
    if len(name_matches) == 1:
        return name_matches[0][1]

    # No unique match found
    return None


# ============================================================================
# Validation on Import
# ============================================================================

def _validate_constants() -> None:
    """Validate that all constants are consistent."""
    # Check counts
    assert len(OLD_TESTAMENT_BOOKS) == 39, "Expected 39 OT books"
    assert len(NEW_TESTAMENT_BOOKS) == 27, "Expected 27 NT books"
    assert len(BOOK_CHAPTERS) == 66, "Expected 66 total books"
    assert len(BOOK_INDEX) == 66, "Expected 66 book indices"
    assert len(BOOK_OSIS) == 66, "Expected 66 OSIS codes"

    # Check all books have entries
    for book in BOOK_CHAPTERS:
        assert book in BOOK_INDEX, f"{book} missing from BOOK_INDEX"
        assert book in BOOK_OSIS, f"{book} missing from BOOK_OSIS"

    # Check indices are 1-66
    indices = sorted(BOOK_INDEX.values())
    assert indices == list(range(1, 67)), "Book indices must be 1-66"


# Validate on import
_validate_constants()


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    print("STEP Constants Module")
    print("=" * 60)
    print(f"Total books: {len(BOOK_CHAPTERS)}")
    print(f"OT books: {len(OLD_TESTAMENT_BOOKS)}")
    print(f"NT books: {len(NEW_TESTAMENT_BOOKS)}")
    print(f"Using Phase 1 constants: {_USING_PHASE1_CONSTANTS}")
    print()

    # Examples
    print("Examples:")
    print(f"  Psalms chapters: {get_chapter_count('Psalms')}")
    print(f"  Genesis OSIS: {get_osis_code('Genesis')}")
    print(f"  Matthew index: {get_book_index('Matthew')}")
    print(f"  Is 'Genesis' OT? {is_old_testament('Genesis')}")
    print(f"  Is 'Matthew' NT? {is_new_testament('Matthew')}")
    print()

    # List first 5 and last 5 books
    all_books = get_all_books_in_order()
    print(f"First 5 books: {all_books[:5]}")
    print(f"Last 5 books: {all_books[-5:]}")
    print()

    print("✓ All validations passed!")
