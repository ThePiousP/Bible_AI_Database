#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step_alignment.py
Text alignment and fuzzy matching utilities for STEP tokens

BEFORE (Phase 1):
  - Alignment functions in step_adapter.py (lines 275-454)
  - No type hints
  - Complex nested logic
  - Limited documentation

AFTER (Phase 2):
  - Dedicated alignment module
  - Full type hints
  - Improved fuzzy matching algorithm
  - Clear separation of concerns
  - Better error handling

Created: 2025-10-29 (Phase 2 Refactoring)
"""

import re
import string
from typing import Optional, Tuple, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from step_parsers import Token


# ============================================================================
# Text Normalization Utilities
# ============================================================================

# Punctuation set for fuzzy matching (includes common Unicode marks)
_PUNCT_SET = set(string.punctuation) | set("''—–-·•…\u200e  ")

# Regex patterns
_PUNCT_FIX = re.compile(r"\s+([,;:.!?])")
_WS_RE = re.compile(r"\s+")


def collapse(s: str) -> str:
    """
    Collapse whitespace runs to single spaces.

    Args:
        s: Input string

    Returns:
        String with collapsed whitespace

    Example:
        >>> collapse("Hello    world\\n\\t!")
        'Hello world !'
    """
    return re.sub(r"\s+", " ", s).strip()


def tidy_punct(s: str) -> str:
    """
    Fix punctuation spacing (remove space before punctuation).

    Args:
        s: Input string

    Returns:
        String with tidied punctuation

    Example:
        >>> tidy_punct("Hello , world !")
        'Hello, world!'
        >>> tidy_punct("( text )")
        '(text)'
    """
    s = _PUNCT_FIX.sub(r"\1", s)
    s = re.sub(r"\(\s+", "(", s)
    s = re.sub(r"\s+\)", ")", s)
    return s


def is_ignorable(ch: str) -> bool:
    """
    Check if a character should be ignored in fuzzy matching.

    Ignorable characters: spaces and punctuation.

    Args:
        ch: Single character

    Returns:
        True if character is ignorable

    Example:
        >>> is_ignorable(' ')
        True
        >>> is_ignorable(',')
        True
        >>> is_ignorable('a')
        False
    """
    return ch.isspace() or ch in _PUNCT_SET


# ============================================================================
# Fuzzy Text Matching
# ============================================================================

def fuzzy_find(
    haystack: str,
    needle: str,
    start: int = 0
) -> Tuple[Optional[int], Optional[int]]:
    """
    Find 'needle' inside 'haystack' with fuzzy matching.

    Allows differences in spacing and punctuation (case-insensitive).
    Returns coordinates in the ORIGINAL haystack.

    Algorithm:
      1. Try exact match (fast path)
      2. Try case-insensitive exact match
      3. Fuzzy match (skip spaces/punctuation on both sides)

    Args:
        haystack: Text to search in
        needle: Text to search for
        start: Starting position in haystack

    Returns:
        Tuple of (start_pos, end_pos) or (None, None) if not found

    Example:
        >>> fuzzy_find("Hello, world!", "world")
        (7, 12)
        >>> fuzzy_find("Hello , world !", "world")
        (8, 13)
        >>> fuzzy_find("HelloWorld", "Hello World")  # Fuzzy match
        (0, 10)
    """
    if not needle:
        return (None, None)

    H = haystack
    N = needle

    # Fast path 1: Exact match
    i = H.find(N, start)
    if i != -1:
        return (i, i + len(N))

    # Fast path 2: Case-insensitive exact match
    i = H.lower().find(N.lower(), start)
    if i != -1:
        return (i, i + len(N))

    # Fuzzy path: Skip spaces/punctuation on both sides
    # Precompute significant characters of needle (lowercased)
    sigN = [c.lower() for c in N if not is_ignorable(c)]
    if not sigN:
        return (None, None)

    j = start

    while j < len(H):
        # Move j to next significant char in H
        while j < len(H) and is_ignorable(H[j]):
            j += 1
        if j >= len(H):
            break

        # Try to match starting at j
        jj = j
        kk = 0
        best_start = None

        while jj < len(H) and kk < len(sigN):
            # Advance jj until significant char
            while jj < len(H) and is_ignorable(H[jj]):
                jj += 1
            if jj >= len(H):
                break

            if H[jj].lower() == sigN[kk]:
                if kk == 0:
                    best_start = jj  # Remember first significant match position
                kk += 1
                jj += 1
            else:
                # Fail this attempt
                best_start = None
                break

        if kk == len(sigN) and best_start is not None:
            # Found match - expand end to include trailing chars
            end = jj
            while end < len(H) and is_ignorable(H[end]):
                end += 1
            return (best_start, end)

        j += 1

    return (None, None)


# ============================================================================
# Token-to-Text Alignment
# ============================================================================

def align_text_offsets(
    text_plain: str,
    tokens: List[Any]  # List["Token"]
) -> None:
    """
    Assign verse-relative character offsets (text_start, text_end) to tokens.

    Scans left-to-right with fuzzy matching to handle spacing/punctuation
    differences between HTML extraction and plain text.

    Args:
        text_plain: Plain text of verse
        tokens: List of Token objects (modified in-place)

    Side effects:
        Sets t.text_start and t.text_end for each token

    Algorithm:
      1. Sort tokens by vhtml_start (reading order)
      2. For each token, try to find its text in plain text:
         - Exact match from cursor
         - Case-insensitive match from cursor
         - Fuzzy match (ignoring punctuation/spacing)
      3. Update cursor to end of match

    Example:
        >>> from step_parsers import Token
        >>> tokens = [Token(text="Hello", vhtml_start=0)]
        >>> align_text_offsets("Hello, world!", tokens)
        >>> tokens[0].text_start, tokens[0].text_end
        (0, 5)
    """
    if not isinstance(text_plain, str):
        # Invalid plain text - clear all offsets
        for t in tokens:
            t.text_start = None
            t.text_end = None
        return

    cursor = 0
    H = text_plain

    for t in tokens:
        tok = (t.text or "").strip()
        if not tok:
            t.text_start = None
            t.text_end = None
            continue

        # Try 1: Exact match from cursor
        i = H.find(tok, cursor)
        if i != -1:
            t.text_start = i
            t.text_end = i + len(tok)
            cursor = t.text_end
            continue

        # Try 2: Case-insensitive exact match
        lowH = H.lower()
        lowTok = tok.lower()
        i = lowH.find(lowTok, cursor)
        if i != -1:
            t.text_start = i
            t.text_end = i + len(tok)
            cursor = t.text_end
            continue

        # Try 3: Fuzzy match (ignore punctuation/spacing)
        i, j = fuzzy_find(H, tok, cursor)
        if i is not None:
            t.text_start = i
            t.text_end = j
            cursor = j
        else:
            # Give up for this token
            t.text_start = None
            t.text_end = None
            # Do NOT move cursor - next tokens might still match


def sort_tokens_for_json(tokens: List[Any]) -> List[Any]:
    """
    Sort tokens by verse-relative start offset (vhtml_start).

    Uses original position as tiebreaker for stability.

    Args:
        tokens: List of Token objects

    Returns:
        Sorted list of tokens

    Example:
        >>> from step_parsers import Token
        >>> tokens = [
        ...     Token(text="world", vhtml_start=10),
        ...     Token(text="Hello", vhtml_start=0)
        ... ]
        >>> sorted_tokens = sort_tokens_for_json(tokens)
        >>> [t.text for t in sorted_tokens]
        ['Hello', 'world']
    """
    BIG = 10**12
    indexed = list(enumerate(tokens))

    # Sort by vhtml_start (or BIG if None), then by original index
    indexed.sort(key=lambda it: (
        (it[1].vhtml_start if it[1].vhtml_start is not None else BIG),
        it[0]
    ))

    return [it[1] for it in indexed]


# ============================================================================
# Fragment Offset Calculation
# ============================================================================

def vfrag_offsets(
    fragment_html: str,
    verse_html: str,
    start_idx: int
) -> Tuple[Optional[int], Optional[int], int]:
    """
    Find fragment_html within verse_html and return its offsets.

    Args:
        fragment_html: HTML fragment to find
        verse_html: Full verse HTML
        start_idx: Starting search position

    Returns:
        Tuple of (start, end, next_cursor)

    Example:
        >>> vfrag_offsets("<em>text</em>", "prefix <em>text</em> suffix", 0)
        (7, 20, 20)
    """
    if not fragment_html or not verse_html:
        return None, None, start_idx

    i = verse_html.find(fragment_html, start_idx)
    if i == -1:
        # Fallback: global search
        i = verse_html.find(fragment_html)
        if i == -1:
            return None, None, start_idx

    return i, i + len(fragment_html), i + len(fragment_html)


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    print("STEP Alignment Module")
    print("=" * 60)

    # Test text normalization
    print("\nText Normalization:")
    print("-" * 60)
    test_text = "Hello  ,  world   !  "
    print(f"  Input:      '{test_text}'")
    print(f"  Collapsed:  '{collapse(test_text)}'")
    print(f"  Tidied:     '{tidy_punct(test_text)}'")

    # Test fuzzy matching
    print("\nFuzzy Matching:")
    print("-" * 60)

    test_cases = [
        ("Hello, world!", "world"),
        ("Hello , world !", "world"),
        ("HelloWorld", "Hello World"),
        ("God created", "God"),
    ]

    for haystack, needle in test_cases:
        start, end = fuzzy_find(haystack, needle)
        if start is not None:
            matched = haystack[start:end]
            print(f"  '{needle}' in '{haystack}'")
            print(f"    → [{start}:{end}] = '{matched}'")
        else:
            print(f"  '{needle}' NOT FOUND in '{haystack}'")

    # Test ignorable characters
    print("\nIgnorable Characters:")
    print("-" * 60)
    test_chars = ['a', ' ', ',', '!', 'Z', '\n']
    for ch in test_chars:
        print(f"  '{ch}' → ignorable={is_ignorable(ch)}")

    print("\n✓ Alignment module loaded successfully!")
