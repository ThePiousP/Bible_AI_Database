#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
silver_label_rules.py
Label matching rules for silver NER dataset

BEFORE (Phase 1):
  - LabelRules class in export_ner_silver.py (lines 81-333)
  - No type hints
  - Complex nested logic

AFTER (Phase 2):
  - Dedicated label rules module
  - Full type hints
  - Clear documentation
  - Better error handling

Created: 2025-10-29 (Phase 2 Refactoring)
"""

import os
import json
import sys
import csv
from typing import Dict, List, Optional, Set, Tuple, Any

# Import data models
from silver_data_models import Token


# ============================================================================
# Label Rules Class
# ============================================================================

class LabelRules:
    """
    Manages label matching rules for NER annotation.

    Supports matching by:
      - Strong's IDs (e.g., "H0430", "G2316")
      - Lemmas (dictionary forms)
      - Surface forms (token text)
      - Multi-word phrases (from gazetteers)

    Features:
      - Per-label case sensitivity
      - Priority-based conflict resolution
      - Phrase override labels
      - Contiguous phrase matching
      - Gazetteer loading (CSV, TSV, TXT, JSON)

    Example:
        >>> rules = LabelRules(config, label_on_miss=None)
        >>> label = rules.label_token(token)
        >>> phrase_labels = rules.phrase_labels_for_tokens(tokens)
    """

    def __init__(self, cfg: Dict[str, Any], label_on_miss: Optional[str] = None) -> None:
        """
        Initialize label rules from configuration.

        Args:
            cfg: Configuration dictionary from label_rules.yml
            label_on_miss: Optional label for unmatched tokens

        Config format:
            labels:
              enabled: [PERSON, LOCATION, DEITY, ...]
              disabled: [...]
            rules:
              PERSON:
                strongs_ids: [H0120, H0376, ...]
                lemmas: [...]
                surfaces: [Adam, Eve, ...]
                case_sensitive: true
                gazetteer_files: [gazetteers/people.txt, ...]
              ...
            merging:
              contiguous_merge: true
            conflicts:
              priority: [DEITY, PERSON, LOCATION, ...]
            phrases:
              override_labels: [PERSON_TITLE, ...]
        """
        self.enabled_labels: List[str] = list(cfg.get("labels", {}).get("enabled", []))
        self.disabled_labels: List[str] = list(cfg.get("labels", {}).get("disabled", []))
        self.rules = cfg.get("rules", {})

        merging_cfg = cfg.get("merging", {})
        self.contiguous_merge: bool = bool(merging_cfg.get("contiguous_merge", True))

        conflicts_cfg = cfg.get("conflicts", {})
        self.priority: List[str] = list(conflicts_cfg.get("priority", self.enabled_labels))

        self.label_on_miss: Optional[str] = label_on_miss

        # Phrase overrides: labels that override per-token labels inside phrases
        phrases_cfg = cfg.get("phrases", {}) if isinstance(cfg, dict) else {}
        self.phrase_override_labels: Set[str] = set(phrases_cfg.get("override_labels", []))

        # Build quick-lookup structures
        self._by_strongs: Dict[str, Set[str]] = {}
        self._by_lemma: Dict[str, Tuple[Set[str], bool]] = {}
        self._by_surface: Dict[str, Tuple[Set[str], bool]] = {}
        self._phrases: Dict[str, Tuple[List[List[str]], bool]] = {}
        self._phrase_heads: Dict[str, Dict[str, List[List[str]]]] = {}

        self._build_lookup_structures()

    def _build_lookup_structures(self) -> None:
        """Build internal lookup structures from rules."""
        for label in self.enabled_labels:
            rr = self.rules.get(label, {})
            sids = rr.get("strongs_ids", []) or []
            lemmas = rr.get("lemmas", []) or []
            surfaces = rr.get("surfaces", []) or []
            case_sensitive = bool(rr.get("case_sensitive", True))

            # Strong's IDs
            for sid in sids:
                sid_norm = sid.strip()
                if sid_norm:
                    self._by_strongs.setdefault(label, set()).add(sid_norm)

            # Lemmas and surfaces
            lemma_set = set(lemmas)
            surface_set = set()
            phrases: List[List[str]] = []
            phrase_heads: Dict[str, List[List[str]]] = {}

            # Process surfaces: split into single words and phrases
            for surf in surfaces:
                if " " in surf:
                    # Multi-word phrase
                    toks = surf.split()
                    if not case_sensitive:
                        toks = [t.lower() for t in toks]
                    phrases.append(toks)
                    head = toks[0]
                    phrase_heads.setdefault(head, []).append(toks)
                else:
                    # Single word
                    s = surf if case_sensitive else surf.lower()
                    surface_set.add(s)

            self._by_lemma[label] = (lemma_set, case_sensitive)
            self._by_surface[label] = (surface_set, case_sensitive)

            # Store phrases from surfaces
            if phrases:
                self._phrases[label] = (phrases, case_sensitive)
                self._phrase_heads[label] = phrase_heads

        # Load gazetteers (merge with any phrases from surfaces)
        for label in self.enabled_labels:
            rr = self.rules.get(label, {})
            gfiles = rr.get("gazetteer_files", []) or []
            if not gfiles:
                continue

            # Get existing surface set and phrases
            if label not in self._by_surface:
                self._by_surface[label] = (set(), True)
            surfaces_set, _ = self._by_surface[label]

            case_sensitive = bool(rr.get("case_sensitive", True))

            # Start with any existing phrases from surfaces list
            if label in self._phrases:
                phrases, _ = self._phrases[label]
                phrases = list(phrases)  # Make a copy
            else:
                phrases = []

            if label in self._phrase_heads:
                phrase_heads = dict(self._phrase_heads[label])  # Make a copy
            else:
                phrase_heads = {}

            for path in gfiles:
                if not os.path.exists(path):
                    print(f"WARN: Gazetteer file not found for {label}: {path}", file=sys.stderr)
                    continue
                loaded = self._load_gazetteer(path)

                for raw in loaded:
                    line = raw.strip()
                    if not line:
                        continue

                    # Multi-word → phrase; single token → surface
                    if " " in line:
                        toks = line.split()
                        if not case_sensitive:
                            toks = [t.lower() for t in toks]
                        phrases.append(toks)
                        head = toks[0]
                        phrase_heads.setdefault(head, []).append(toks)
                    else:
                        s = line if case_sensitive else line.lower()
                        surfaces_set.add(s)

            # Save back
            self._by_surface[label] = (surfaces_set, case_sensitive)
            if phrases:
                self._phrases[label] = (phrases, case_sensitive)
                self._phrase_heads[label] = phrase_heads

    @staticmethod
    def _load_gazetteer(path: str) -> Set[str]:
        """
        Load gazetteer from file.

        Supports:
          - CSV/TSV: First column is the surface string
          - TXT: One entry per line (# for comments)
          - JSON: list[str] or list[dict] with 'name' key

        Args:
            path: Path to gazetteer file

        Returns:
            Set of gazetteer entries
        """
        ext = os.path.splitext(path)[1].lower()
        results: Set[str] = set()

        if ext in (".csv", ".tsv"):
            delim = "," if ext == ".csv" else "\t"
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=delim)
                for row in reader:
                    if not row:
                        continue
                    s = row[0].strip()
                    if s:
                        results.add(s)

        elif ext == ".txt":
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    results.add(s)

        elif ext == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, str):
                        s = item.strip()
                        if s:
                            results.add(s)
                    elif isinstance(item, dict):
                        name = str(item.get("name", "")).strip()
                        if name:
                            results.add(name)
        else:
            print(f"WARN: Unsupported gazetteer type {ext}; skipping {path}", file=sys.stderr)

        return results

    def phrase_labels_for_tokens(self, tokens: List[Token]) -> List[Optional[str]]:
        """
        Assign phrase labels to tokens (per-token basis).

        Uses contiguous matching: tokens must match phrase exactly (no gaps).
        Resolves conflicts using global priority list.

        Args:
            tokens: List of Token objects

        Returns:
            List of labels (one per token), None if no match

        Example:
            >>> tokens = [Token("King"), Token("David")]
            >>> rules.phrase_labels_for_tokens(tokens)
            ['PERSON_TITLE', 'PERSON_TITLE']
        """
        n = len(tokens)
        best: List[Optional[str]] = [None] * n

        # Precompute priority index
        prio_index = {lab: i for i, lab in enumerate(self.priority)}

        for label, heads in self._phrase_heads.items():
            cs = bool(self.rules.get(label, {}).get("case_sensitive", True))
            surfaces = [t.surface if cs else (t.surface or "").lower() for t in tokens]
            label_prio = prio_index.get(label, 10**9)

            for i in range(n):
                head = surfaces[i]
                cand_list = heads.get(head)
                if not cand_list:
                    continue

                for phrase in cand_list:
                    m = len(phrase)
                    if i + m > n:
                        continue

                    # Exact contiguous match
                    if surfaces[i:i+m] == phrase:
                        # Mark all tokens in window
                        for k in range(i, i+m):
                            cur = best[k]
                            if cur is None:
                                best[k] = label
                            else:
                                # Keep higher priority (lower index)
                                if prio_index.get(cur, 10**9) > label_prio:
                                    best[k] = label

        return best

    def phrase_override_mask(self, tokens: List[Token]) -> List[Optional[str]]:
        """
        Return per-token mask of override phrase labels.

        Override labels (configured in phrases.override_labels) take precedence
        over per-token labels within the matched phrase window.

        Args:
            tokens: List of Token objects

        Returns:
            List of override labels (one per token), None if no override

        Example:
            >>> tokens = [Token("King"), Token("David")]
            >>> rules.phrase_override_mask(tokens)
            ['PERSON_TITLE', 'PERSON_TITLE']
        """
        n = len(tokens)
        if not self.phrase_override_labels:
            return [None] * n

        mask: List[Optional[str]] = [None] * n
        prio_index = {lab: i for i, lab in enumerate(self.priority)}

        # Walk labels in priority order (earlier wins)
        for label in self.priority:
            if label not in self.phrase_override_labels:
                continue

            heads = self._phrase_heads.get(label)
            if not heads:
                continue

            cs = bool(self.rules.get(label, {}).get("case_sensitive", True))
            surfaces = [t.surface if cs else (t.surface or "").lower() for t in tokens]

            for i in range(n):
                cand_list = heads.get(surfaces[i])
                if not cand_list:
                    continue

                for phrase in cand_list:
                    m = len(phrase)
                    if i + m > n:
                        continue

                    if surfaces[i:i+m] == phrase:
                        # Apply override across entire phrase window
                        for k in range(i, i+m):
                            if mask[k] is None:
                                mask[k] = label

        return mask

    def label_token(self, tok: Token) -> Optional[str]:
        """
        Determine single label for token (or None).

        Matches by:
          1. Strong's ID
          2. Lemma
          3. Surface form

        Resolves conflicts using priority list.

        Args:
            tok: Token object

        Returns:
            Label string or None

        Example:
            >>> token = Token(surface="God", strongs_id="H0430")
            >>> rules.label_token(token)
            'DEITY'
        """
        candidates: Set[str] = set()

        # Strong's match
        if tok.strongs_id:
            for label, sids in self._by_strongs.items():
                if tok.strongs_id in sids:
                    candidates.add(label)

        # Lemma match
        if tok.lemma:
            for label, (lemmas, case_sensitive) in self._by_lemma.items():
                key = tok.lemma if case_sensitive else tok.lemma.lower()
                lookup = lemmas if case_sensitive else {l.lower() for l in lemmas}
                if key in lookup:
                    candidates.add(label)

        # Surface match
        surface = tok.surface or ""
        if surface:
            for label, (surfaces, case_sensitive) in self._by_surface.items():
                key = surface if case_sensitive else surface.lower()
                if key in (surfaces if case_sensitive else {s.lower() for s in surfaces}):
                    candidates.add(label)

        if not candidates:
            return self.label_on_miss if getattr(self, 'label_on_miss', None) else None

        # Resolve conflicts by priority
        for pref in self.priority:
            if pref in candidates:
                return pref

        return next(iter(candidates))


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    print("Silver NER Label Rules Module")
    print("=" * 60)

    # Example configuration
    config = {
        "labels": {
            "enabled": ["DEITY", "PERSON", "LOCATION"],
            "disabled": []
        },
        "rules": {
            "DEITY": {
                "strongs_ids": ["H0430", "G2316"],
                "lemmas": ["אֱלֹהִים", "θεός"],
                "surfaces": ["God", "LORD"],
                "case_sensitive": False
            },
            "PERSON": {
                "strongs_ids": [],
                "lemmas": [],
                "surfaces": ["Adam", "Eve", "Noah"],
                "case_sensitive": True
            }
        },
        "conflicts": {
            "priority": ["DEITY", "PERSON", "LOCATION"]
        },
        "merging": {
            "contiguous_merge": True
        }
    }

    rules = LabelRules(config)
    print(f"\nEnabled labels: {rules.enabled_labels}")
    print(f"Priority: {rules.priority}")

    # Test token labeling
    token1 = Token(surface="God", strongs_id="H0430")
    print(f"\nLabel for {token1.surface} ({token1.strongs_id}): {rules.label_token(token1)}")

    token2 = Token(surface="Adam")
    print(f"Label for {token2.surface}: {rules.label_token(token2)}")

    print("\n✓ Label rules module loaded successfully!")
