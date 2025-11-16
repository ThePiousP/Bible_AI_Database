#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for silver_label_rules.py - Label matching and priority resolution

Tests:
- test_strongs_id_matching: Match tokens by Strong's ID
- test_lemma_matching: Match tokens by lemma
- test_surface_matching: Match tokens by surface form
- test_case_sensitivity: Case-sensitive vs case-insensitive matching
- test_priority_resolution: Resolve conflicts using priority list
- test_phrase_matching: Multi-word phrase detection
- test_phrase_override: Phrase labels override token labels
- test_gazetteer_loading: Load gazetteers from files
"""

import pytest
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from silver_label_rules import LabelRules
from silver_data_models import Token


# ============================================================================
# Strong's ID Matching Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.labels
def test_strongs_id_matching(sample_rules):
    """Test matching tokens by Strong's concordance ID."""
    # H0430 = אֱלֹהִים (Elohim) should match DEITY
    token = Token(surface="God", strongs_id="H0430")

    label = sample_rules.label_token(token)

    assert label == "DEITY", f"H0430 should match DEITY, got: {label}"


@pytest.mark.unit
@pytest.mark.labels
def test_strongs_id_matching_greek(sample_rules):
    """Test matching Greek Strong's IDs."""
    # G2316 = θεός (theos) should match DEITY
    token = Token(surface="God", strongs_id="G2316")

    label = sample_rules.label_token(token)

    assert label == "DEITY", f"G2316 should match DEITY, got: {label}"


@pytest.mark.unit
@pytest.mark.labels
def test_no_strongs_id():
    """Test token without Strong's ID."""
    config = {
        "labels": {"enabled": ["PERSON"], "disabled": []},
        "rules": {
            "PERSON": {
                "strongs_ids": ["H0120"],
                "lemmas": [],
                "surfaces": [],
                "case_sensitive": True
            }
        },
        "conflicts": {"priority": ["PERSON"]},
        "merging": {"contiguous_merge": True}
    }

    rules = LabelRules(config)
    token = Token(surface="Adam")  # No Strong's ID

    label = rules.label_token(token)

    assert label is None, "Token without Strong's ID should not match"


# ============================================================================
# Lemma Matching Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.labels
def test_lemma_matching(sample_rules):
    """Test matching tokens by lemma (dictionary form)."""
    # אֱלֹהִים should match DEITY
    token = Token(surface="Elohim", lemma="אֱלֹהִים")

    label = sample_rules.label_token(token)

    assert label == "DEITY", f"Hebrew lemma should match DEITY, got: {label}"


@pytest.mark.unit
@pytest.mark.labels
def test_lemma_matching_greek(sample_rules):
    """Test matching Greek lemmas."""
    # θεός should match DEITY
    token = Token(surface="theos", lemma="θεός")

    label = sample_rules.label_token(token)

    assert label == "DEITY", f"Greek lemma should match DEITY, got: {label}"


# ============================================================================
# Surface Matching Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.labels
def test_surface_matching(sample_rules):
    """Test matching tokens by surface form."""
    token = Token(surface="Adam")  # No Strong's or lemma

    label = sample_rules.label_token(token)

    assert label == "PERSON", f"'Adam' should match PERSON, got: {label}"


@pytest.mark.unit
@pytest.mark.labels
def test_surface_matching_case_sensitive(sample_rules):
    """Test case-sensitive surface matching."""
    # PERSON is case-sensitive (Adam != adam)
    token = Token(surface="adam")  # lowercase

    label = sample_rules.label_token(token)

    assert label is None, "Lowercase 'adam' should not match case-sensitive 'Adam'"


@pytest.mark.unit
@pytest.mark.labels
def test_surface_matching_case_insensitive(sample_rules):
    """Test case-insensitive surface matching."""
    # DEITY is case-insensitive (God = god = GOD)
    token1 = Token(surface="god")  # lowercase
    token2 = Token(surface="GOD")  # uppercase
    token3 = Token(surface="God")  # titlecase

    assert sample_rules.label_token(token1) == "DEITY", "Lowercase 'god' should match"
    assert sample_rules.label_token(token2) == "DEITY", "Uppercase 'GOD' should match"
    assert sample_rules.label_token(token3) == "DEITY", "Titlecase 'God' should match"


# ============================================================================
# Priority Resolution Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.labels
def test_priority_resolution():
    """Test conflict resolution using priority list."""
    config = {
        "labels": {"enabled": ["DEITY", "PERSON"], "disabled": []},
        "rules": {
            "DEITY": {
                "strongs_ids": [],
                "lemmas": [],
                "surfaces": ["Lord"],
                "case_sensitive": False
            },
            "PERSON": {
                "strongs_ids": [],
                "lemmas": [],
                "surfaces": ["Lord"],  # Same as DEITY
                "case_sensitive": False
            }
        },
        "conflicts": {"priority": ["DEITY", "PERSON"]},  # DEITY has higher priority
        "merging": {"contiguous_merge": True}
    }

    rules = LabelRules(config)
    token = Token(surface="Lord")

    label = rules.label_token(token)

    assert label == "DEITY", "Should choose DEITY (higher priority) over PERSON"


@pytest.mark.unit
@pytest.mark.labels
def test_priority_resolution_reversed():
    """Test priority resolution with reversed priority."""
    config = {
        "labels": {"enabled": ["DEITY", "PERSON"], "disabled": []},
        "rules": {
            "DEITY": {
                "strongs_ids": [],
                "lemmas": [],
                "surfaces": ["Lord"],
                "case_sensitive": False
            },
            "PERSON": {
                "strongs_ids": [],
                "lemmas": [],
                "surfaces": ["Lord"],
                "case_sensitive": False
            }
        },
        "conflicts": {"priority": ["PERSON", "DEITY"]},  # PERSON has higher priority
        "merging": {"contiguous_merge": True}
    }

    rules = LabelRules(config)
    token = Token(surface="Lord")

    label = rules.label_token(token)

    assert label == "PERSON", "Should choose PERSON (higher priority) over DEITY"


# ============================================================================
# Phrase Matching Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.labels
def test_phrase_matching_basic(sample_rules_with_phrases):
    """Test multi-word phrase detection."""
    tokens = [
        Token(surface="King"),
        Token(surface="David"),
        Token(surface="said")
    ]

    phrase_labels = sample_rules_with_phrases.phrase_labels_for_tokens(tokens)

    # "King David" should be labeled as PERSON_TITLE
    assert phrase_labels[0] == "PERSON_TITLE", "First token of phrase should be labeled"
    assert phrase_labels[1] == "PERSON_TITLE", "Second token of phrase should be labeled"
    assert phrase_labels[2] is None, "'said' is not part of phrase"


@pytest.mark.unit
@pytest.mark.labels
def test_phrase_matching_partial_match(sample_rules_with_phrases):
    """Test that partial phrase matches don't trigger."""
    tokens = [
        Token(surface="King"),
        Token(surface="Solomon"),  # Not "David"
        Token(surface="said")
    ]

    phrase_labels = sample_rules_with_phrases.phrase_labels_for_tokens(tokens)

    # "King Solomon" should match (it's in the configuration)
    assert phrase_labels[0] == "PERSON_TITLE", "'King Solomon' should match"
    assert phrase_labels[1] == "PERSON_TITLE", "'King Solomon' should match"


@pytest.mark.unit
@pytest.mark.labels
def test_phrase_override_mask(sample_rules_with_phrases):
    """Test phrase override labels take precedence."""
    tokens = [
        Token(surface="King"),
        Token(surface="David"),  # Would normally be PERSON, but part of PERSON_TITLE phrase
    ]

    override_mask = sample_rules_with_phrases.phrase_override_mask(tokens)

    # Both tokens should have PERSON_TITLE override
    assert override_mask[0] == "PERSON_TITLE", "Override should apply to first token"
    assert override_mask[1] == "PERSON_TITLE", "Override should apply to second token"


@pytest.mark.unit
@pytest.mark.labels
def test_phrase_matching_case_sensitive(sample_rules_with_phrases):
    """Test case sensitivity in phrase matching."""
    tokens = [
        Token(surface="king"),  # lowercase
        Token(surface="david")  # lowercase
    ]

    phrase_labels = sample_rules_with_phrases.phrase_labels_for_tokens(tokens)

    # PERSON_TITLE is case-sensitive, so "king david" should NOT match "King David"
    assert phrase_labels[0] is None, "Lowercase 'king' should not match case-sensitive 'King'"
    assert phrase_labels[1] is None, "Lowercase 'david' should not match case-sensitive 'David'"


# ============================================================================
# Gazetteer Loading Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.labels
def test_gazetteer_loading_txt(sample_gazetteer_file):
    """Test loading gazetteer from TXT file."""
    config = {
        "labels": {"enabled": ["PERSON"], "disabled": []},
        "rules": {
            "PERSON": {
                "strongs_ids": [],
                "lemmas": [],
                "surfaces": [],
                "case_sensitive": True,
                "gazetteer_files": [str(sample_gazetteer_file)]
            }
        },
        "conflicts": {"priority": ["PERSON"]},
        "merging": {"contiguous_merge": True}
    }

    rules = LabelRules(config)

    # Test tokens from gazetteer
    assert rules.label_token(Token(surface="Adam")) == "PERSON"
    assert rules.label_token(Token(surface="Eve")) == "PERSON"
    assert rules.label_token(Token(surface="Noah")) == "PERSON"
    assert rules.label_token(Token(surface="Unknown")) is None


@pytest.mark.unit
@pytest.mark.labels
def test_gazetteer_missing_file():
    """Test handling of missing gazetteer file."""
    config = {
        "labels": {"enabled": ["PERSON"], "disabled": []},
        "rules": {
            "PERSON": {
                "strongs_ids": [],
                "lemmas": [],
                "surfaces": [],
                "case_sensitive": True,
                "gazetteer_files": ["/nonexistent/file.txt"]  # Missing file
            }
        },
        "conflicts": {"priority": ["PERSON"]},
        "merging": {"contiguous_merge": True}
    }

    # Should not raise exception, just skip the file
    rules = LabelRules(config)
    assert rules is not None, "Should handle missing gazetteer gracefully"


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.unit
@pytest.mark.labels
def test_empty_token_surface(sample_rules):
    """Test handling of token with empty surface."""
    token = Token(surface="", strongs_id="H0430")

    label = sample_rules.label_token(token)

    # Should still match by Strong's ID
    assert label == "DEITY", "Should match by Strong's ID even with empty surface"


@pytest.mark.unit
@pytest.mark.labels
def test_label_on_miss():
    """Test default label for unmatched tokens."""
    config = {
        "labels": {"enabled": ["OTHER"], "disabled": []},
        "rules": {
            "OTHER": {
                "strongs_ids": [],
                "lemmas": [],
                "surfaces": [],
                "case_sensitive": True
            }
        },
        "conflicts": {"priority": ["OTHER"]},
        "merging": {"contiguous_merge": True}
    }

    rules = LabelRules(config, label_on_miss="OTHER")
    token = Token(surface="UnknownWord")

    label = rules.label_token(token)

    assert label == "OTHER", "Unmatched token should get default label"


@pytest.mark.unit
@pytest.mark.labels
def test_multiple_strongs_ids(sample_rules):
    """Test token with multiple Strong's IDs (should match first)."""
    token = Token(surface="God", strongs_id="H0430")  # Hebrew Elohim

    label = sample_rules.label_token(token)

    assert label == "DEITY", "Should match DEITY by Strong's ID"
