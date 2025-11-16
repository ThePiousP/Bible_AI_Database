#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for silver_alignment.py - Greedy text alignment algorithm

Tests:
- test_perfect_alignment: All tokens align perfectly
- test_alignment_with_missing_token: One token doesn't match
- test_alignment_with_whitespace_variations: Handle extra spaces
- test_alignment_preserves_order: Tokens match in order
- test_build_spans_basic: Build spans from aligned tokens
- test_build_spans_with_merging: Merge contiguous same-label spans
- test_calculate_alignment_stats: Compute alignment statistics
"""

import pytest
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from silver_alignment import (
    greedy_align_tokens_to_text,
    build_spans,
    build_spans_with_phrases,
    calculate_alignment_stats
)
from silver_data_models import Verse, Token, Span


# ============================================================================
# Greedy Alignment Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.alignment
def test_perfect_alignment(sample_verse_text, sample_tokens):
    """Test alignment with perfect match."""
    spans, misses = greedy_align_tokens_to_text(sample_verse_text, sample_tokens)

    assert misses == 0, "Should have no alignment misses"
    assert len(spans) == len(sample_tokens), "Should have one span per token"

    # Check specific alignments
    assert spans[0] == (0, 2), "First token 'In' should be at [0:2]"
    assert spans[1] == (3, 6), "Second token 'the' should be at [3:6]"
    assert spans[2] == (7, 16), "Third token 'beginning' should be at [7:16]"
    assert spans[3] == (17, 20), "Fourth token 'God' should be at [17:20]"
    assert spans[4] == (21, 28), "Fifth token 'created' should be at [21:28]"

    # Verify all spans are valid (start < end)
    for start, end in spans:
        assert start >= 0, f"Start position should be non-negative: {start}"
        assert end > start, f"End should be after start: [{start}:{end}]"


@pytest.mark.unit
@pytest.mark.alignment
def test_alignment_with_missing_token():
    """Test alignment when a token is not found in text."""
    text = "In the beginning God created"
    tokens = ["In", "the", "MISSING", "beginning", "God", "created"]

    spans, misses = greedy_align_tokens_to_text(text, tokens)

    assert misses == 1, "Should have exactly 1 miss"
    assert spans[2] == (-1, -1), "Missing token should have (-1, -1) span"

    # Other tokens should still align correctly
    assert spans[0] == (0, 2), "First token should align"
    assert spans[1] == (3, 6), "Second token should align"
    assert spans[3] == (7, 16), "Fourth token should align after miss"
    assert spans[4] == (17, 20), "Fifth token should align"


@pytest.mark.unit
@pytest.mark.alignment
def test_alignment_with_whitespace_variations():
    """Test alignment with extra spaces in text."""
    text = "In  the  beginning  God  created"  # Double spaces
    tokens = ["In", "the", "beginning", "God", "created"]

    spans, misses = greedy_align_tokens_to_text(text, tokens)

    # Should still find all tokens (greedy matching)
    assert misses == 0, "Should handle whitespace variations"
    assert len(spans) == 5, "Should align all tokens"


@pytest.mark.unit
@pytest.mark.alignment
def test_alignment_preserves_order():
    """Test that alignment matches tokens in left-to-right order."""
    text = "the book the table the chair"  # "the" appears 3 times
    tokens = ["the", "book", "the", "table", "the", "chair"]

    spans, misses = greedy_align_tokens_to_text(text, tokens)

    assert misses == 0, "All tokens should align"

    # Verify left-to-right ordering (each "the" matches next occurrence)
    assert spans[0] == (0, 3), "First 'the' at position 0"
    assert spans[2] == (9, 12), "Second 'the' at position 9"
    assert spans[4] == (19, 22), "Third 'the' at position 19"

    # Verify spans are non-overlapping and ordered
    for i in range(len(spans) - 1):
        assert spans[i][1] <= spans[i+1][0], f"Spans should not overlap: {spans[i]} vs {spans[i+1]}"


@pytest.mark.unit
@pytest.mark.alignment
def test_empty_token_alignment():
    """Test alignment with empty token."""
    text = "In the beginning"
    tokens = ["In", "", "the", "beginning"]

    spans, misses = greedy_align_tokens_to_text(text, tokens)

    assert misses == 1, "Empty token should be a miss"
    assert spans[1] == (-1, -1), "Empty token should have (-1, -1)"
    assert spans[0] == (0, 2), "Non-empty tokens should still align"
    assert spans[2] == (3, 6), "Non-empty tokens should still align"


# ============================================================================
# Build Spans Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.alignment
def test_build_spans_basic(sample_verse, sample_rules):
    """Test building spans from aligned tokens."""
    spans = build_spans(sample_verse, sample_rules)

    # Should have at least one span for "God" (DEITY)
    assert len(spans) > 0, "Should create at least one span"

    # Find the God span
    god_spans = [s for s in spans if s.label == "DEITY"]
    assert len(god_spans) > 0, "Should label 'God' as DEITY"

    # Verify the God span is correct
    god_span = god_spans[0]
    assert sample_verse.text[god_span.start:god_span.end] == "God", \
        f"Span should match 'God' in text: {sample_verse.text[god_span.start:god_span.end]}"


@pytest.mark.unit
@pytest.mark.alignment
def test_build_spans_with_merging(sample_rules):
    """Test contiguous span merging."""
    # Create verse with two consecutive DEITY tokens
    tokens = [
        Token(surface="the"),
        Token(surface="LORD", strongs_id="H3068"),  # DEITY
        Token(surface="God", strongs_id="H0430"),    # DEITY (contiguous)
        Token(surface="said")
    ]

    verse = Verse(
        verse_id=1,
        book="Test",
        chapter=1,
        verse=1,
        text="the LORD God said",
        tokens=tokens,
        align_spans=[]
    )

    # With contiguous_merge=True (default)
    spans = build_spans(verse, sample_rules)

    # Should merge "LORD God" into single span
    deity_spans = [s for s in spans if s.label == "DEITY"]
    assert len(deity_spans) == 1, "Should merge contiguous DEITY spans"

    # Verify merged span covers both tokens
    deity_span = deity_spans[0]
    assert verse.text[deity_span.start:deity_span.end] == "LORD God", \
        f"Merged span should cover 'LORD God': {verse.text[deity_span.start:deity_span.end]}"


@pytest.mark.unit
@pytest.mark.alignment
def test_build_spans_with_phrases(sample_verse_with_person, sample_rules_with_phrases):
    """Test phrase matching (multi-word entities)."""
    # Create verse with "King David"
    tokens = [
        Token(surface="And"),
        Token(surface="King"),
        Token(surface="David"),
        Token(surface="said")
    ]

    verse = Verse(
        verse_id=1,
        book="Test",
        chapter=1,
        verse=1,
        text="And King David said",
        tokens=tokens,
        align_spans=[]
    )

    spans = build_spans_with_phrases(verse, sample_rules_with_phrases)

    # Should match "King David" as PERSON_TITLE (not separate PERSON tokens)
    title_spans = [s for s in spans if s.label == "PERSON_TITLE"]
    assert len(title_spans) > 0, "Should detect 'King David' phrase"

    # Verify the phrase span
    title_span = title_spans[0]
    assert verse.text[title_span.start:title_span.end] == "King David", \
        f"Phrase span should cover 'King David': {verse.text[title_span.start:title_span.end]}"


# ============================================================================
# Alignment Statistics Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.alignment
def test_calculate_alignment_stats(sample_verse):
    """Test alignment statistics calculation."""
    # Create list with one verse
    verses = [sample_verse]

    # Manually set align_spans for testing
    sample_verse.align_spans = [
        (0, 2),    # Aligned
        (3, 6),    # Aligned
        (-1, -1),  # Unaligned
        (7, 16),   # Aligned
        (17, 20),  # Aligned
    ]

    stats = calculate_alignment_stats(verses)

    assert stats['total_tokens'] == 5, "Should count 5 tokens"
    assert stats['aligned'] == 4, "Should have 4 aligned tokens"
    assert stats['unaligned'] == 1, "Should have 1 unaligned token"
    assert stats['success_rate'] == 0.8, "Success rate should be 80%"


@pytest.mark.unit
@pytest.mark.alignment
def test_calculate_alignment_stats_empty():
    """Test alignment statistics with empty list."""
    stats = calculate_alignment_stats([])

    assert stats['total_tokens'] == 0
    assert stats['aligned'] == 0
    assert stats['unaligned'] == 0
    assert stats['success_rate'] == 0.0
    assert stats['avg_verse_length'] == 0.0
    assert stats['avg_tokens_per_verse'] == 0.0


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.unit
@pytest.mark.alignment
def test_alignment_with_repeated_words():
    """Test alignment with same word appearing multiple times."""
    text = "God created God blessed God saw"
    tokens = ["God", "created", "God", "blessed", "God", "saw"]

    spans, misses = greedy_align_tokens_to_text(text, tokens)

    assert misses == 0, "All tokens should align"

    # Verify each "God" matches the next occurrence
    assert spans[0] == (0, 3), "First 'God'"
    assert spans[2] == (12, 15), "Second 'God'"
    assert spans[4] == (24, 27), "Third 'God'"


@pytest.mark.unit
@pytest.mark.alignment
def test_alignment_with_special_characters():
    """Test alignment with punctuation and special characters."""
    text = "In the beginning, God created."
    tokens = ["In", "the", "beginning", "God", "created"]

    spans, misses = greedy_align_tokens_to_text(text, tokens)

    # Tokens without punctuation should still match
    assert misses == 0, "Should align despite punctuation in text"
    assert spans[2] == (7, 16), "'beginning' should match before comma"
    assert spans[4] == (22, 29), "'created' should match before period"
