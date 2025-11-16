#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for STEP normalization and text utilities

Tests cover:
- Strong's number normalization
- Morphology code normalization
- Text utility functions (collapse, tidy_punct)
"""

import pytest
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code" / "STEP"
sys.path.insert(0, str(code_dir))

from step_normalization import normalize_strongs, normalize_morph
from step_alignment import collapse, tidy_punct


# ============================================================================
# Strong's Number Normalization Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.parsing
def test_normalize_strongs_hebrew():
    """Test normalizing Hebrew Strong's number."""
    norm, raw = normalize_strongs("H430")

    assert norm == "H0430", f"Should normalize to H0430, got: {norm}"
    assert raw == "H430", "Should preserve raw value"


@pytest.mark.unit
@pytest.mark.parsing
def test_normalize_strongs_greek():
    """Test normalizing Greek Strong's number."""
    norm, raw = normalize_strongs("G2316")

    assert norm == "G2316", f"Should keep G2316 as is, got: {norm}"
    assert raw == "G2316", "Should preserve raw value"


@pytest.mark.unit
@pytest.mark.parsing
def test_normalize_strongs_with_padding():
    """Test Strong's number that needs padding."""
    norm, raw = normalize_strongs("H1")

    assert norm == "H0001", f"Should pad to H0001, got: {norm}"
    assert raw == "H1", "Should preserve raw value"


@pytest.mark.unit
@pytest.mark.parsing
def test_normalize_strongs_multiple():
    """Test Strong's with multiple numbers (keeps first)."""
    norm, raw = normalize_strongs("H430 H776")

    assert norm == "H0430", f"Should take first number, got: {norm}"
    assert raw == "H430 H776", "Should preserve full raw value"


@pytest.mark.unit
@pytest.mark.parsing
def test_normalize_strongs_none():
    """Test Strong's normalization with None."""
    norm, raw = normalize_strongs(None)

    assert norm is None, "Should return None"
    assert raw is None, "Should return None"


@pytest.mark.unit
@pytest.mark.parsing
def test_normalize_strongs_empty():
    """Test Strong's normalization with empty string."""
    norm, raw = normalize_strongs("")

    assert norm is None, "Should return None for empty string"
    assert raw is None, "Should return None for empty string"


# ============================================================================
# Morphology Normalization Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.parsing
def test_normalize_morph_with_prefix():
    """Test morphology normalization with strongMorph prefix."""
    norm, raw = normalize_morph("strongMorph:N-NSM")

    assert norm == "N-NSM", f"Should strip prefix, got: {norm}"
    assert raw == "strongMorph:N-NSM", "Should preserve raw value"


@pytest.mark.unit
@pytest.mark.parsing
def test_normalize_morph_without_prefix():
    """Test morphology normalization without prefix."""
    norm, raw = normalize_morph("V-AAI-3S")

    assert norm == "V-AAI-3S", "Should keep as is"
    assert raw == "V-AAI-3S", "Should preserve raw value"


@pytest.mark.unit
@pytest.mark.parsing
def test_normalize_morph_none():
    """Test morphology normalization with None."""
    norm, raw = normalize_morph(None)

    assert norm is None, "Should return None"
    assert raw is None, "Should return None"


@pytest.mark.unit
@pytest.mark.parsing
def test_normalize_morph_empty():
    """Test morphology normalization with empty string."""
    norm, raw = normalize_morph("")

    assert norm is None, "Should return None for empty string"
    assert raw is None, "Should return None for empty string"


# ============================================================================
# Text Utility Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.parsing
def test_collapse_whitespace():
    """Test whitespace collapsing."""
    text = "In  the   beginning"
    result = collapse(text)

    assert result == "In the beginning", f"Should collapse to single spaces, got: '{result}'"
    assert "  " not in result, "Should not have double spaces"


@pytest.mark.unit
@pytest.mark.parsing
def test_collapse_with_tabs_newlines():
    """Test collapsing tabs and newlines."""
    text = "In\tthe\nbeginning"
    result = collapse(text)

    assert "\t" not in result, "Should remove tabs"
    assert "\n" not in result, "Should remove newlines"
    assert result == "In the beginning", f"Should collapse to single spaces, got: '{result}'"


@pytest.mark.unit
@pytest.mark.parsing
def test_tidy_punct_basic():
    """Test basic punctuation tidying."""
    text = "Hello , world !"
    result = tidy_punct(text)

    # tidy_punct removes space before punctuation
    assert result == "Hello, world!", f"Should remove space before punct, got: '{result}'"


@pytest.mark.unit
@pytest.mark.parsing
def test_tidy_punct_preserves_letters():
    """Test that tidy_punct preserves letters."""
    text = "God"
    result = tidy_punct(text)

    assert result == "God", "Should preserve letters"


@pytest.mark.unit
@pytest.mark.parsing
def test_tidy_punct_removes_quotes():
    """Test that tidy_punct handles parentheses."""
    text = "( Hello )"
    result = tidy_punct(text)

    # tidy_punct removes space inside parentheses
    assert result == "(Hello)", f"Should remove space in parens, got: '{result}'"


@pytest.mark.unit
@pytest.mark.parsing
def test_collapse_empty_string():
    """Test collapsing empty string."""
    result = collapse("")

    assert result == "", "Empty string should remain empty"


@pytest.mark.unit
@pytest.mark.parsing
def test_tidy_punct_empty_string():
    """Test tidying empty string."""
    result = tidy_punct("")

    assert result == "", "Empty string should remain empty"


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.parsing
def test_normalize_strongs_pipeline():
    """Test typical Strong's normalization pipeline."""
    # Typical raw value from STEP XML
    raw_strongs = "strongMorph:H0430"

    # Extract the part after colon
    if ":" in raw_strongs:
        extracted = raw_strongs.split(":", 1)[1]
    else:
        extracted = raw_strongs

    norm, raw = normalize_strongs(extracted)

    assert norm == "H0430", f"Should normalize to H0430, got: {norm}"


@pytest.mark.unit
@pytest.mark.parsing
def test_text_normalization_pipeline():
    """Test typical text normalization pipeline."""
    # Raw text from XML
    raw_text = "In  the\n  beginning ,  God"

    # Step 1: Collapse whitespace
    collapsed = collapse(raw_text)

    # Step 2: Tidy punctuation
    tidied = tidy_punct(collapsed)

    assert "  " not in collapsed, "Should collapse multiple spaces"
    assert "\n" not in collapsed, "Should remove newlines"
    assert collapsed == "In the beginning , God", "Should collapse whitespace"
    assert tidied == "In the beginning, God", "Should remove space before comma"
