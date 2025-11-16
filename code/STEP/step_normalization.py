#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step_normalization.py
Strong's number and morphology normalization for STEP data

BEFORE (Phase 1):
  - Normalization functions scattered in step_adapter.py (lines 94-137, 455-486)
  - No type hints
  - Global state (_MORPH_MAP_CACHE)
  - Basic error handling

AFTER (Phase 2):
  - Dedicated normalization module
  - Full type hints
  - Better error handling
  - Cached morph map loading
  - Clear separation of concerns

Created: 2025-10-29 (Phase 2 Refactoring)
"""

import re
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Final


# ============================================================================
# Strong's Number Normalization
# ============================================================================

# Regex for parsing Strong's numbers (H0430, G5624, etc.)
_STRONG_RE: Final[re.Pattern] = re.compile(r"^([HG]\d{3,4})([A-Z])?$")


def format_strongs_norm(s: Optional[str]) -> Optional[str]:
    """
    Format a Strong's number to canonical H#### or G#### format.

    Args:
        s: Raw Strong's number (e.g., "H430", "G5624", "h1")

    Returns:
        Normalized format (e.g., "H0430", "G5624"), or None if invalid

    Example:
        >>> format_strongs_norm("H430")
        'H0430'
        >>> format_strongs_norm("g1")
        'G0001'
        >>> format_strongs_norm(None)
        None
    """
    if not s:
        return None

    s = s.strip()
    if not s or len(s) < 2:
        return s

    # Extract prefix (H/G) and digits
    prefix = s[0].upper()
    if prefix not in ('H', 'G'):
        return s

    digits = ''.join(ch for ch in s[1:] if ch.isdigit())
    if not digits:
        return s

    # Format as H#### or G####
    return f"{prefix}{int(digits):04d}"


def normalize_strongs(raw: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalize Strong's number(s), keeping the first normalized value.

    Handles multiple Strong's numbers separated by spaces, commas, slashes, etc.
    Returns the FIRST valid Strong's number found (normalized) and preserves raw.

    Args:
        raw: Raw Strong's string (e.g., "H0430 H0776", "G2316/G2962")

    Returns:
        Tuple of (normalized_first, raw_preserved)

    Example:
        >>> normalize_strongs("H430 H776")
        ('H0430', 'H430 H776')
        >>> normalize_strongs("G2316/G2962")
        ('G2316', 'G2316/G2962')
        >>> normalize_strongs(None)
        (None, None)
    """
    if not raw:
        return None, None

    # Collapse whitespace
    s = " ".join(str(raw).split())

    # Split on common delimiters
    parts = [p for p in re.split(r"[\s,;/]+", s) if p]

    norm_first: Optional[str] = None

    # Try to find first valid Strong's number
    for part in parts:
        m = _STRONG_RE.match(part)
        if m:
            norm_first = format_strongs_norm(m.group(1))
            break

        # Fallback: check if starts with H/G
        if part and part[0] in ("H", "G", "h", "g"):
            norm_first = format_strongs_norm(part)
            break

    # Last resort: try first part
    if not norm_first and parts:
        norm_first = format_strongs_norm(parts[0])

    return norm_first, raw


# ============================================================================
# Morphology Normalization
# ============================================================================

def normalize_morph(raw: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalize morphology code, stripping prefixes like "strongMorph:".

    Args:
        raw: Raw morph string (e.g., "strongMorph:N-NSM", "V-AAI-3S")

    Returns:
        Tuple of (normalized, raw_preserved)

    Example:
        >>> normalize_morph("strongMorph:N-NSM")
        ('N-NSM', 'strongMorph:N-NSM')
        >>> normalize_morph("V-AAI-3S")
        ('V-AAI-3S', 'V-AAI-3S')
        >>> normalize_morph(None)
        (None, None)
    """
    if not raw:
        return None, None

    # Strip "strongMorph:" prefix if present
    if raw.startswith("strongMorph:"):
        normalized = raw.split(":", 1)[1]
        return normalized, raw

    # No normalization needed
    return raw, raw


# ============================================================================
# Morphology Map Loading & Decoding
# ============================================================================

_MORPH_MAP_CACHE: Optional[Dict[str, Any]] = None


def load_morph_map(path: str = "morph_map.json") -> Optional[Dict[str, Any]]:
    """
    Load morphology mapping from JSON file (cached).

    The morph_map.json file maps morphology codes to human-readable glosses
    and grammatical features.

    Args:
        path: Path to morph_map.json file

    Returns:
        Dictionary mapping morph codes to metadata, or None if not found

    Example structure:
        {
            "N-NSM": {
                "gloss": "Noun, Nominative, Singular, Masculine",
                "features": {"pos": "N", "case": "Nom", "number": "Sing", "gender": "Masc"}
            },
            ...
        }
    """
    global _MORPH_MAP_CACHE

    # Return cached value if available
    if _MORPH_MAP_CACHE is not None:
        return _MORPH_MAP_CACHE

    # Try to load from file
    morph_path = Path(path)
    if not morph_path.exists():
        _MORPH_MAP_CACHE = None
        return None

    try:
        data = json.loads(morph_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            _MORPH_MAP_CACHE = data
            return data
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        # Silently fail if file can't be loaded
        pass

    _MORPH_MAP_CACHE = None
    return None


def decode_morph(
    morph_norm: Optional[str],
    morph_raw: Optional[str]
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Decode morphology code to gloss and features using morph_map.json.

    Args:
        morph_norm: Normalized morph code
        morph_raw: Raw morph code

    Returns:
        Tuple of (gloss, features_dict)

    Example:
        >>> decode_morph("N-NSM", "strongMorph:N-NSM")
        ('Noun, Nominative, Singular, Masculine', {'pos': 'N', 'case': 'Nom', ...})
    """
    morph_map = load_morph_map()
    if not morph_map:
        return None, None

    # Try normalized first, then raw
    for key in (morph_norm, morph_raw):
        if not key:
            continue

        hit = morph_map.get(key)
        if isinstance(hit, dict):
            gloss = hit.get("gloss")
            features = hit.get("features")
            if isinstance(features, dict):
                return gloss, features
            else:
                return gloss, None

    return None, None


def reset_morph_cache() -> None:
    """
    Reset the morphology map cache.

    Useful for testing or when morph_map.json is updated at runtime.
    """
    global _MORPH_MAP_CACHE
    _MORPH_MAP_CACHE = None


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    print("STEP Normalization Module")
    print("=" * 60)

    # Strong's normalization examples
    print("\nStrong's Number Normalization:")
    print("-" * 60)

    test_strongs = [
        "H430",
        "H0430",
        "h1",
        "G2316",
        "G5624",
        "g100",
        "H430 H776",      # Multiple
        "G2316/G2962",    # Separated by slash
        None,
        "",
    ]

    for raw in test_strongs:
        norm, preserved = normalize_strongs(raw)
        print(f"  {str(raw):20s} → normalized={norm}, preserved={preserved}")

    # Morphology normalization examples
    print("\nMorphology Normalization:")
    print("-" * 60)

    test_morphs = [
        "N-NSM",
        "strongMorph:N-NSM",
        "V-AAI-3S",
        "strongMorph:V-AAI-3S",
        None,
        "",
    ]

    for raw in test_morphs:
        norm, preserved = normalize_morph(raw)
        print(f"  {str(raw):30s} → normalized={norm}")

    # Morph map loading (if available)
    print("\nMorphology Map:")
    print("-" * 60)
    morph_map = load_morph_map()
    if morph_map:
        print(f"  Loaded {len(morph_map)} morphology mappings")
        # Show a sample entry
        sample_key = list(morph_map.keys())[0] if morph_map else None
        if sample_key:
            print(f"  Sample: {sample_key} → {morph_map[sample_key]}")

        # Test decoding
        gloss, features = decode_morph("N-NSM", None)
        print(f"  Decoded 'N-NSM': gloss={gloss}, features={features}")
    else:
        print("  (morph_map.json not found - this is optional)")

    print("\n✓ Normalization module loaded successfully!")
