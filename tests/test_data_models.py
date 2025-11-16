#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for silver_data_models.py

Tests data structures used in the NER pipeline:
- Token: Individual word with linguistic annotations
- Verse: Container for tokens and verse metadata
- Span: Labeled entity span
- NERExample: Training example for spaCy
"""

import pytest
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from silver_data_models import Token, Verse, Span, NERExample


# ============================================================================
# Token Tests
# ============================================================================

@pytest.mark.unit
def test_token_basic_creation():
    """Test basic Token creation."""
    token = Token(surface="God")

    assert token.surface == "God"
    assert token.strongs_id is None
    assert token.lemma is None
    assert token.pos is None


@pytest.mark.unit
def test_token_with_strongs():
    """Test Token with Strong's ID."""
    token = Token(
        surface="God",
        strongs_id="H0430",
        lemma="אֱלֹהִים"
    )

    assert token.surface == "God"
    assert token.strongs_id == "H0430"
    assert token.lemma == "אֱלֹהִים"


@pytest.mark.unit
def test_token_with_all_fields():
    """Test Token with all fields populated."""
    token = Token(
        surface="created",
        strongs_id="H1254",
        lemma="בָּרָא",
        pos="Verb"
    )

    assert token.surface == "created"
    assert token.strongs_id == "H1254"
    assert token.lemma == "בָּרָא"
    assert token.pos == "Verb"


@pytest.mark.unit
def test_token_equality():
    """Test Token equality comparison."""
    token1 = Token(surface="God", strongs_id="H0430")
    token2 = Token(surface="God", strongs_id="H0430")
    token3 = Token(surface="God", strongs_id="H3068")

    assert token1 == token2, "Identical tokens should be equal"
    assert token1 != token3, "Different tokens should not be equal"


# ============================================================================
# Verse Tests
# ============================================================================

@pytest.mark.unit
def test_verse_basic_creation():
    """Test basic Verse creation."""
    verse = Verse(
        verse_id=1,
        book="Genesis",
        chapter=1,
        verse=1,
        text="In the beginning God created",
        tokens=[]
    )

    assert verse.verse_id == 1
    assert verse.book == "Genesis"
    assert verse.chapter == 1
    assert verse.verse == 1
    assert verse.text == "In the beginning God created"
    assert len(verse.tokens) == 0


@pytest.mark.unit
def test_verse_with_tokens():
    """Test Verse with tokens."""
    tokens = [
        Token(surface="In"),
        Token(surface="the"),
        Token(surface="beginning"),
        Token(surface="God", strongs_id="H0430"),
    ]

    verse = Verse(
        verse_id=1,
        book="Genesis",
        chapter=1,
        verse=1,
        text="In the beginning God",
        tokens=tokens
    )

    assert len(verse.tokens) == 4
    assert verse.tokens[3].surface == "God"
    assert verse.tokens[3].strongs_id == "H0430"


@pytest.mark.unit
def test_verse_with_align_spans():
    """Test Verse with alignment spans."""
    verse = Verse(
        verse_id=1,
        book="Genesis",
        chapter=1,
        verse=1,
        text="In the beginning",
        tokens=[Token(surface="In"), Token(surface="the"), Token(surface="beginning")],
        align_spans=[(0, 2), (3, 6), (7, 16)]
    )

    assert len(verse.align_spans) == 3
    assert verse.align_spans[0] == (0, 2)
    assert verse.align_spans[2] == (7, 16)


# ============================================================================
# Span Tests
# ============================================================================

@pytest.mark.unit
def test_span_basic_creation():
    """Test basic Span creation."""
    span = Span(start=0, end=5, label="DEITY")

    assert span.start == 0
    assert span.end == 5
    assert span.label == "DEITY"


@pytest.mark.unit
def test_span_ordering():
    """Test Span ordering by start position."""
    span1 = Span(start=0, end=5, label="DEITY")
    span2 = Span(start=10, end=15, label="PERSON")
    span3 = Span(start=5, end=8, label="LOCATION")

    spans = [span2, span3, span1]
    sorted_spans = sorted(spans, key=lambda s: s.start)

    assert sorted_spans[0].start == 0
    assert sorted_spans[1].start == 5
    assert sorted_spans[2].start == 10


@pytest.mark.unit
def test_span_equality():
    """Test Span equality."""
    span1 = Span(start=0, end=5, label="DEITY")
    span2 = Span(start=0, end=5, label="DEITY")
    span3 = Span(start=0, end=5, label="PERSON")

    assert span1 == span2, "Identical spans should be equal"
    assert span1 != span3, "Spans with different labels should not be equal"


@pytest.mark.unit
def test_span_length():
    """Test calculating span length."""
    span = Span(start=10, end=20, label="PERSON")

    length = span.end - span.start
    assert length == 10


# ============================================================================
# NERExample Tests
# ============================================================================

@pytest.mark.unit
def test_ner_example_basic():
    """Test basic NERExample creation."""
    example = NERExample(
        text="In the beginning God created",
        spans=[Span(start=17, end=20, label="DEITY")]
    )

    assert example.text == "In the beginning God created"
    assert len(example.spans) == 1
    assert example.spans[0].label == "DEITY"


@pytest.mark.unit
def test_ner_example_multiple_spans():
    """Test NERExample with multiple spans."""
    example = NERExample(
        text="The LORD God created Adam",
        spans=[
            Span(start=4, end=8, label="DEITY"),
            Span(start=9, end=12, label="DEITY"),
            Span(start=21, end=25, label="PERSON")
        ]
    )

    assert len(example.spans) == 3
    assert example.spans[0].label == "DEITY"
    assert example.spans[2].label == "PERSON"


@pytest.mark.unit
def test_ner_example_to_json():
    """Test NERExample JSON serialization format."""
    example = NERExample(
        text="God created",
        spans=[Span(start=0, end=3, label="DEITY")]
    )

    # Verify it has the right structure for spaCy/Prodigy
    assert hasattr(example, "text")
    assert hasattr(example, "spans")
    assert example.spans[0].start == 0
    assert example.spans[0].end == 3
    assert example.spans[0].label == "DEITY"


@pytest.mark.unit
def test_ner_example_empty_spans():
    """Test NERExample with no spans."""
    example = NERExample(
        text="In the beginning",
        spans=[]
    )

    assert example.text == "In the beginning"
    assert len(example.spans) == 0


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.unit
def test_verse_to_ner_example():
    """Test converting Verse to NERExample."""
    # Create verse with tokens
    tokens = [
        Token(surface="In"),
        Token(surface="the"),
        Token(surface="beginning"),
        Token(surface="God", strongs_id="H0430"),
    ]

    verse = Verse(
        verse_id=1,
        book="Genesis",
        chapter=1,
        verse=1,
        text="In the beginning God",
        tokens=tokens,
        align_spans=[(0, 2), (3, 6), (7, 16), (17, 20)]
    )

    # Create span for "God"
    spans = [Span(start=17, end=20, label="DEITY")]

    # Create NER example
    example = NERExample(text=verse.text, spans=spans)

    assert example.text == verse.text
    assert len(example.spans) == 1
    assert example.text[example.spans[0].start:example.spans[0].end] == "God"


@pytest.mark.unit
def test_token_list_with_mixed_annotations():
    """Test list of tokens with varying annotation completeness."""
    tokens = [
        Token(surface="In"),  # No annotations
        Token(surface="the"),  # No annotations
        Token(surface="beginning"),  # No annotations
        Token(surface="God", strongs_id="H0430", lemma="אֱלֹהִים"),  # Partial
        Token(
            surface="created",
            strongs_id="H1254",
            lemma="בָּרָא",
            pos="Verb"
        ),  # Full annotations
    ]

    # Verify mixed annotation levels
    assert tokens[0].strongs_id is None
    assert tokens[3].strongs_id == "H0430"
    assert tokens[4].pos == "Verb"

    # All should have surface text
    for token in tokens:
        assert token.surface is not None


@pytest.mark.unit
def test_span_extraction_from_text():
    """Test extracting text using span coordinates."""
    text = "In the beginning God created the heaven"
    spans = [
        Span(start=17, end=20, label="DEITY"),
        Span(start=33, end=39, label="LOCATION")
    ]

    # Extract text for each span
    extracted = [text[s.start:s.end] for s in spans]

    assert extracted[0] == "God"
    assert extracted[1] == "heaven"


@pytest.mark.unit
def test_verse_reference_string():
    """Test generating verse reference strings."""
    verse = Verse(
        verse_id=1,
        book="Genesis",
        chapter=1,
        verse=1,
        text="In the beginning God created",
        tokens=[]
    )

    reference = f"{verse.book} {verse.chapter}:{verse.verse}"
    assert reference == "Genesis 1:1"
