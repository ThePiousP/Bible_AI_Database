#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared pytest fixtures for Bible NER Pipeline tests

Fixtures:
- sample_verse: Simple verse for basic tests
- sample_tokens: Token list for alignment tests
- sample_label_config: Label rules configuration
- sample_rules: LabelRules instance
"""

import pytest
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from silver_data_models import Token, Verse, Span
from silver_label_rules import LabelRules


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_verse_text() -> str:
    """Genesis 1:1 text."""
    return "In the beginning God created the heaven and the earth."


@pytest.fixture
def sample_tokens() -> list[str]:
    """Token surfaces for Genesis 1:1."""
    return ["In", "the", "beginning", "God", "created", "the", "heaven", "and", "the", "earth"]


@pytest.fixture
def sample_verse(sample_verse_text, sample_tokens) -> Verse:
    """Complete Verse object with tokens."""
    tokens = [
        Token(surface="In"),
        Token(surface="the"),
        Token(surface="beginning"),
        Token(surface="God", strongs_id="H0430", lemma="אֱלֹהִים", pos="Noun"),
        Token(surface="created", strongs_id="H1254", lemma="בָּרָא", pos="Verb"),
        Token(surface="the"),
        Token(surface="heaven", strongs_id="H8064", lemma="שָׁמַיִם", pos="Noun"),
        Token(surface="and"),
        Token(surface="the"),
        Token(surface="earth", strongs_id="H0776", lemma="אֶרֶץ", pos="Noun"),
    ]

    return Verse(
        verse_id=1,
        book="Genesis",
        chapter=1,
        verse=1,
        text=sample_verse_text,
        tokens=tokens,
        align_spans=[]
    )


@pytest.fixture
def sample_verse_with_person() -> Verse:
    """Verse with person entity (Genesis 2:19)."""
    tokens = [
        Token(surface="And"),
        Token(surface="out"),
        Token(surface="of"),
        Token(surface="the"),
        Token(surface="ground"),
        Token(surface="the"),
        Token(surface="LORD", strongs_id="H3068", lemma="יְהוָה"),
        Token(surface="God", strongs_id="H0430", lemma="אֱלֹהִים"),
        Token(surface="formed"),
        Token(surface="every"),
        Token(surface="beast"),
    ]

    return Verse(
        verse_id=2,
        book="Genesis",
        chapter=2,
        verse=19,
        text="And out of the ground the LORD God formed every beast",
        tokens=tokens,
        align_spans=[]
    )


# ============================================================================
# Label Rules Fixtures
# ============================================================================

@pytest.fixture
def sample_label_config() -> dict:
    """Minimal label rules configuration for testing."""
    return {
        "labels": {
            "enabled": ["DEITY", "PERSON", "LOCATION"],
            "disabled": []
        },
        "rules": {
            "DEITY": {
                "strongs_ids": ["H0430", "H3068", "G2316", "G2962"],
                "lemmas": ["אֱלֹהִים", "יְהוָה", "θεός", "κύριος"],
                "surfaces": ["God", "LORD", "Lord"],
                "case_sensitive": False,
                "gazetteer_files": []
            },
            "PERSON": {
                "strongs_ids": [],
                "lemmas": [],
                "surfaces": ["Adam", "Eve", "Noah", "Abraham", "Moses", "David"],
                "case_sensitive": True,
                "gazetteer_files": []
            },
            "LOCATION": {
                "strongs_ids": [],
                "lemmas": [],
                "surfaces": ["Eden", "Egypt", "Jerusalem", "Babylon"],
                "case_sensitive": True,
                "gazetteer_files": []
            }
        },
        "conflicts": {
            "priority": ["DEITY", "PERSON", "LOCATION"]
        },
        "merging": {
            "contiguous_merge": True
        },
        "phrases": {
            "override_labels": []
        }
    }


@pytest.fixture
def sample_rules(sample_label_config) -> LabelRules:
    """LabelRules instance with sample configuration."""
    return LabelRules(sample_label_config, label_on_miss=None)


@pytest.fixture
def sample_label_config_with_phrases() -> dict:
    """Label configuration with phrase matching."""
    return {
        "labels": {
            "enabled": ["DEITY", "PERSON", "PERSON_TITLE"],
            "disabled": []
        },
        "rules": {
            "DEITY": {
                "strongs_ids": ["H0430", "H3068"],
                "lemmas": [],
                "surfaces": ["God", "LORD"],
                "case_sensitive": False,
                "gazetteer_files": []
            },
            "PERSON": {
                "strongs_ids": [],
                "lemmas": [],
                "surfaces": ["David", "Solomon", "Moses"],
                "case_sensitive": True,
                "gazetteer_files": []
            },
            "PERSON_TITLE": {
                "strongs_ids": [],
                "lemmas": [],
                "surfaces": ["King David", "King Solomon", "Son of Man"],
                "case_sensitive": True,
                "gazetteer_files": []
            }
        },
        "conflicts": {
            "priority": ["DEITY", "PERSON_TITLE", "PERSON"]
        },
        "merging": {
            "contiguous_merge": True
        },
        "phrases": {
            "override_labels": ["PERSON_TITLE"]
        }
    }


@pytest.fixture
def sample_rules_with_phrases(sample_label_config_with_phrases) -> LabelRules:
    """LabelRules instance with phrase matching."""
    return LabelRules(sample_label_config_with_phrases, label_on_miss=None)


# ============================================================================
# Span Fixtures
# ============================================================================

@pytest.fixture
def sample_spans() -> list[Span]:
    """Sample labeled spans."""
    return [
        Span(start=0, end=10, label="PERSON"),
        Span(start=20, end=30, label="LOCATION"),
        Span(start=40, end=50, label="DEITY")
    ]


# ============================================================================
# Morphology Fixtures
# ============================================================================

@pytest.fixture
def sample_hebrew_morph() -> str:
    """Sample Hebrew morphology code."""
    return "HNcmsa"  # Noun, common, masculine, singular, absolute


@pytest.fixture
def sample_greek_morph() -> str:
    """Sample Greek morphology code."""
    return "V-AAI-3S"  # Verb, Aorist, Active, Indicative, 3rd person, Singular


# ============================================================================
# XML Fixtures
# ============================================================================

@pytest.fixture
def sample_step_xml() -> str:
    """Sample STEP XML fragment."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<verse osisID="Gen.1.1" canonical="true">
    <w lemma="strong:H7225" morph="robinson:HNcfsa" n="1.0">בְּרֵאשִׁ֖ית</w>
    <w lemma="strong:H1254" morph="robinson:HVqp3ms" n="1.1">בָּרָ֣א</w>
    <w lemma="strong:H0430" morph="robinson:HNcmpa" n="1.2">אֱלֹהִ֑ים</w>
    <w lemma="strong:H0853" morph="robinson:HTo" n="1.3">אֵ֥ת</w>
    <w lemma="strong:H8064" morph="robinson:HNcmpa" n="1.4">הַשָּׁמַ֖יִם</w>
    <w lemma="strong:H0853" morph="robinson:HTo" n="1.5">וְאֵ֥ת</w>
    <w lemma="strong:H0776" morph="robinson:HNcfsa" n="1.6">הָאָֽרֶץ׃</w>
</verse>"""


# ============================================================================
# Test Data Paths
# ============================================================================

@pytest.fixture
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_gazetteer_file(tmp_path) -> Path:
    """Create temporary gazetteer file."""
    gazetteer = tmp_path / "test_people.txt"
    gazetteer.write_text("Adam\nEve\nNoah\nAbraham\nMoses\nDavid\n", encoding="utf-8")
    return gazetteer


# ============================================================================
# Helper Functions
# ============================================================================

def assert_span_equal(span1: Span, span2: Span) -> None:
    """Assert two spans are equal."""
    assert span1.start == span2.start, f"Span start mismatch: {span1.start} != {span2.start}"
    assert span1.end == span2.end, f"Span end mismatch: {span1.end} != {span2.end}"
    assert span1.label == span2.label, f"Span label mismatch: {span1.label} != {span2.label}"


def assert_token_equal(token1: Token, token2: Token) -> None:
    """Assert two tokens are equal."""
    assert token1.surface == token2.surface
    assert token1.strongs_id == token2.strongs_id
    assert token1.lemma == token2.lemma
    assert token1.pos == token2.pos
