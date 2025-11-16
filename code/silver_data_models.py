#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
silver_data_models.py
Data structures for silver NER dataset export

BEFORE (Phase 1):
  - Data classes embedded in export_ner_silver.py (lines 52-76)
  - Basic dataclasses without extensive documentation

AFTER (Phase 2):
  - Dedicated data models module
  - Full type hints
  - Comprehensive documentation
  - Clear separation of concerns

Created: 2025-10-29 (Phase 2 Refactoring)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ============================================================================
# Token Data Model
# ============================================================================

@dataclass
class Token:
    """
    Represents a single token/word with linguistic annotations.

    Attributes:
        surface: The text of the token (e.g., "God", "created")
        strongs_id: Strong's concordance ID (e.g., "H0430", "G2316")
        lemma: Lemma/dictionary form in original language
        pos: Part of speech tag

    Example:
        >>> token = Token(surface="God", strongs_id="H0430", lemma="אֱלֹהִים")
        >>> token.surface
        'God'
        >>> token.strongs_id
        'H0430'
    """
    surface: str
    strongs_id: Optional[str] = None
    lemma: Optional[str] = None
    pos: Optional[str] = None


# ============================================================================
# Verse Data Model
# ============================================================================

@dataclass
class Verse:
    """
    Represents a single Bible verse with tokens and alignment information.

    Attributes:
        verse_id: Unique verse ID from database
        book: Book name (e.g., "Genesis", "Matthew")
        chapter: Chapter number (1-indexed)
        verse: Verse number (1-indexed)
        text: Plain text of the verse (from verses.text_plain)
        tokens: List of tokens in database order (token_idx)
        align_spans: Character offsets for each token in text
                     [(start, end), ...] aligned to text

    Example:
        >>> verse = Verse(
        ...     verse_id=1,
        ...     book="Genesis",
        ...     chapter=1,
        ...     verse=1,
        ...     text="In the beginning God created the heaven and the earth.",
        ...     tokens=[Token("In"), Token("the"), Token("beginning"), ...],
        ...     align_spans=[(0, 2), (3, 6), (7, 16), ...]
        ... )
        >>> verse.book
        'Genesis'
        >>> len(verse.tokens)
        11
    """
    verse_id: int
    book: str
    chapter: int
    verse: int
    text: str
    tokens: List[Token]
    align_spans: List[Tuple[int, int]] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation of verse reference."""
        return f"{self.book} {self.chapter}:{self.verse}"

    def get_ref(self) -> str:
        """Get verse reference string."""
        return f"{self.book}.{self.chapter}.{self.verse}"


# ============================================================================
# Span Data Model
# ============================================================================

@dataclass
class Span:
    """
    Represents a labeled text span (entity) in NER format.

    Attributes:
        start: Character offset of span start (0-indexed)
        end: Character offset of span end (exclusive)
        label: Entity label (e.g., "PERSON", "LOCATION", "DEITY")

    Example:
        >>> span = Span(start=0, end=3, label="DEITY")
        >>> span.label
        'DEITY'
        >>> span.start, span.end
        (0, 3)
    """
    start: int
    end: int
    label: str

    def __len__(self) -> int:
        """Length of the span in characters."""
        return self.end - self.start

    def __str__(self) -> str:
        """String representation of span."""
        return f"[{self.start}:{self.end}]={self.label}"

    def overlaps(self, other: 'Span') -> bool:
        """
        Check if this span overlaps with another span.

        Args:
            other: Another Span object

        Returns:
            True if spans overlap, False otherwise

        Example:
            >>> span1 = Span(0, 10, "A")
            >>> span2 = Span(5, 15, "B")
            >>> span1.overlaps(span2)
            True
            >>> span3 = Span(20, 30, "C")
            >>> span1.overlaps(span3)
            False
        """
        return not (self.end <= other.start or other.end <= self.start)

    def contains(self, other: 'Span') -> bool:
        """
        Check if this span fully contains another span.

        Args:
            other: Another Span object

        Returns:
            True if this span contains other, False otherwise

        Example:
            >>> outer = Span(0, 20, "A")
            >>> inner = Span(5, 10, "B")
            >>> outer.contains(inner)
            True
            >>> inner.contains(outer)
            False
        """
        return self.start <= other.start and other.end <= self.end


# ============================================================================
# NER Example Data Model
# ============================================================================

@dataclass
class NERExample:
    """
    Represents a complete NER training example in spaCy/Prodigy format.

    Attributes:
        text: Plain text string
        spans: List of labeled spans
        meta: Optional metadata (book, chapter, verse, etc.)

    Example:
        >>> example = NERExample(
        ...     text="In the beginning God created",
        ...     spans=[Span(17, 20, "DEITY")],
        ...     meta={"book": "Genesis", "chapter": 1, "verse": 1}
        ... )
        >>> example.to_dict()
        {
            'text': 'In the beginning God created',
            'spans': [{'start': 17, 'end': 20, 'label': 'DEITY'}],
            'meta': {'book': 'Genesis', 'chapter': 1, 'verse': 1}
        }
    """
    text: str
    spans: List[Span]
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON export.

        Returns:
            Dictionary in spaCy training format

        Format:
            {
                'text': str,
                'spans': [{'start': int, 'end': int, 'label': str}, ...],
                'meta': {...}
            }
        """
        return {
            'text': self.text,
            'spans': [
                {'start': s.start, 'end': s.end, 'label': s.label}
                for s in self.spans
            ],
            'meta': self.meta
        }

    def to_prodigy_format(self) -> dict:
        """
        Convert to Prodigy annotation format.

        Returns:
            Dictionary in Prodigy format

        Format:
            {
                'text': str,
                'spans': [{'start': int, 'end': int, 'label': str, 'token_start': int, 'token_end': int}, ...],
                'meta': {...}
            }
        """
        # For now, same as to_dict() - can extend with token indices later
        return self.to_dict()


# ============================================================================
# Schema Information
# ============================================================================

@dataclass
class SchemaInfo:
    """
    Database schema information.

    Attributes:
        has_text_plain: Whether verses.text_plain column exists
        has_text_clean: Whether verses.text_clean column exists
        text_prefer: Which text column to prefer ("auto", "clean", "plain")
        text_column: Resolved SQL column name to use

    Example:
        >>> schema = SchemaInfo(
        ...     has_text_plain=True,
        ...     has_text_clean=True,
        ...     text_prefer="clean",
        ...     text_column="text_clean"
        ... )
        >>> schema.text_column
        'text_clean'
    """
    has_text_plain: bool
    has_text_clean: bool
    text_prefer: str
    text_column: str


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    print("Silver NER Data Models Module")
    print("=" * 60)

    # Example Token
    token = Token(surface="God", strongs_id="H0430", lemma="אֱלֹהִים", pos="Noun")
    print(f"\nToken: {token.surface} ({token.strongs_id})")

    # Example Verse
    verse = Verse(
        verse_id=1,
        book="Genesis",
        chapter=1,
        verse=1,
        text="In the beginning God created the heaven and the earth.",
        tokens=[Token("In"), Token("the"), Token("beginning"), Token("God")],
        align_spans=[(0, 2), (3, 6), (7, 16), (17, 20)]
    )
    print(f"\nVerse: {verse}")
    print(f"  Text: {verse.text}")
    print(f"  Tokens: {len(verse.tokens)}")

    # Example Span
    span = Span(start=17, end=20, label="DEITY")
    print(f"\nSpan: {span}")
    print(f"  Length: {len(span)} chars")

    # Test span operations
    span1 = Span(0, 10, "A")
    span2 = Span(5, 15, "B")
    span3 = Span(2, 8, "C")
    print(f"\nSpan operations:")
    print(f"  {span1} overlaps {span2}: {span1.overlaps(span2)}")
    print(f"  {span1} contains {span3}: {span1.contains(span3)}")

    # Example NER Example
    example = NERExample(
        text="In the beginning God created",
        spans=[span],
        meta={"book": "Genesis", "chapter": 1, "verse": 1}
    )
    print(f"\nNER Example:")
    print(f"  {example.to_dict()}")

    print("\n✓ Data models module loaded successfully!")
