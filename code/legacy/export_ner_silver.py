#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export a silver NER dataset from concordance.db using simple, auditable label rules.
This version uses GREEDY ALIGNMENT of token surfaces to verses.text_plain
(instead of trusting stored char offsets), which fixes mismatches between
DB offsets and plain text.

- Reads verse text (fixed normalized join: books -> chapters -> verses)
- Pulls tokens by verse_id, ordered by token_idx, and uses token.text
- Greedily aligns token surfaces into verses.text_plain to compute (start,end)
- Applies label rules from YAML (by Strong's id, lemma, optional surface/gazetteers)
- Merges contiguous tokens with the same label into single spans
- Splits into train/dev/test with stratification by book (80/10/10 default)
- Optional holdout by books

No edits to existing project files. This is a standalone script.

Requirements:
  - Python 3.9+
  - pyyaml

Usage (posix):
  python export_ner_silver.py --db ./concordance.db --rules ./label_rules.yml --outdir ./silver_out

Usage (Windows):
  python export_ner_silver.py --db C:\\BIBLE\\concordance.db --rules .\\label_rules.yml --outdir .\\silver_out
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import random
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Set

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# -------------------------
# Data classes / types
# -------------------------
@dataclass
class Token:
    surface: str
    strongs_id: Optional[str] = None
    lemma: Optional[str] = None
    pos: Optional[str] = None


@dataclass
class Verse:
    verse_id: int
    book: str
    chapter: int
    verse: int
    text: str                 # verses.text_plain
    tokens: List[Token]       # DB-order (token_idx)
    align_spans: List[Tuple[int, int]]  # per-token (start,end) in text_plain (computed)


@dataclass
class Span:
    start: int
    end: int
    label: str


# -------------------------
# Label rules loader
# -------------------------
class LabelRules:
    def __init__(self, cfg: Dict[str, Any], label_on_miss: Optional[str] = None) -> None:
        self.enabled_labels: List[str] = list(cfg.get("labels", {}).get("enabled", []))
        self.disabled_labels: List[str] = list(cfg.get("labels", {}).get("disabled", []))
        self.rules = cfg.get("rules", {})
        merging_cfg = cfg.get("merging", {})
        self.contiguous_merge: bool = bool(merging_cfg.get("contiguous_merge", True))
        conflicts_cfg = cfg.get("conflicts", {})
        self.priority: List[str] = list(conflicts_cfg.get("priority", self.enabled_labels))
        self.label_on_miss: Optional[str] = label_on_miss
        
        # Phrase overrides: labels that should override any per-token label inside the phrase
        phrases_cfg = cfg.get("phrases", {}) if isinstance(cfg, dict) else {}
        self.phrase_override_labels: Set[str] = set(phrases_cfg.get("override_labels", []))

        # Build quick-lookup sets, respecting per-label case sensitivity
        self._by_strongs: Dict[str, Set[str]] = {}
        self._by_lemma: Dict[str, Tuple[Set[str], bool]] = {}
        self._by_surface: Dict[str, Tuple[Set[str], bool]] = {}

        # NEW: phrase storage and first-token index per label
        self._phrases: Dict[str, Tuple[List[List[str]], bool]] = {}
        self._phrase_heads: Dict[str, Dict[str, List[List[str]]]] = {}        

        for label in self.enabled_labels:
            rr = self.rules.get(label, {})
            sids = rr.get("strongs_ids", []) or []
            lemmas = rr.get("lemmas", []) or []
            surfaces = rr.get("surfaces", []) or []
            case_sensitive = bool(rr.get("case_sensitive", True))

            for sid in sids:
                sid_norm = sid.strip()
                if sid_norm:
                    self._by_strongs.setdefault(label, set()).add(sid_norm)

            lemma_set = set(lemmas)
            surface_set = set(surfaces)
            self._by_lemma[label] = (lemma_set, case_sensitive)
            self._by_surface[label] = (surface_set, case_sensitive)

        # Gazetteers (optional): split lines into single-token surfaces vs multi-token phrases
        for label in self.enabled_labels:
            rr = self.rules.get(label, {})
            gfiles = rr.get("gazetteer_files", []) or []
            if not gfiles:
                continue

            # ensure we have surface and phrase slots
            if label not in self._by_surface:
                self._by_surface[label] = (set(), True)
            surfaces_set, _ = self._by_surface[label]

            case_sensitive = bool(rr.get("case_sensitive", True))
            phrases: List[List[str]] = []
            phrase_heads: Dict[str, List[List[str]]] = {}

            for path in gfiles:
                if not os.path.exists(path):
                    print(f"WARN: Gazetteer file not found for {label}: {path}", file=sys.stderr)
                    continue
                loaded = self._load_gazetteer(path)

                for raw in loaded:
                    line = raw.strip()
                    if not line:
                        continue
                    # multi-word → phrase; single token → surface
                    if " " in line:
                        # phrase tokens normalized per case-sensitivity
                        toks = line.split()
                        if not case_sensitive:
                            toks = [t.lower() for t in toks]
                        phrases.append(toks)
                        head = toks[0]
                        phrase_heads.setdefault(head, []).append(toks)
                    else:
                        s = line if case_sensitive else line.lower()
                        surfaces_set.add(s)

            # save back
            self._by_surface[label] = (surfaces_set, case_sensitive)
            if phrases:
                self._phrases[label] = (phrases, case_sensitive)
                self._phrase_heads[label] = phrase_heads


    @staticmethod
    def _load_gazetteer(path: str) -> Set[str]:
        """
        Accept very simple CSV/JSON:
        - CSV: first column treated as the surface string headerless
        - JSON: list[str] or list[dict] with key 'name'
        """
        ext = os.path.splitext(path)[1].lower()
        results: Set[str] = set()
        if ext in (".csv", ".tsv"):
            import csv
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
        For each token position, return the best phrase label (if any) that covers it,
        using per-label case sensitivity and global conflicts.priority for tie-breaks.
        Matching is contiguous: tokens must match the phrase tokens exactly (no gaps).
        """
        n = len(tokens)
        best: List[Optional[str]] = [None] * n

        # precompute priority index for speed
        prio_index = {lab: i for i, lab in enumerate(self.priority)}

        for label, heads in self._phrase_heads.items():
            # pull case flag for this label
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
                    # exact contiguous match
                    if surfaces[i:i+m] == phrase:
                        # mark all tokens in the window
                        for k in range(i, i+m):
                            cur = best[k]
                            if cur is None:
                                best[k] = label
                            else:
                                # keep higher priority (lower index)
                                if prio_index.get(cur, 10**9) > label_prio:
                                    best[k] = label
                        # allow overlapping matches; do not skip ahead
        return best

    def phrase_override_mask(self, tokens: List[Token]) -> List[Optional[str]]:
        """
        Return a per-token mask of override phrase labels.
        Any label listed in self.phrase_override_labels will 'stick' across the entire matched phrase
        (i.e., it overrides other labels within the phrase window).
        Overlaps are resolved by global conflicts.priority: earlier (higher-priority) labels win.
        """
        n = len(tokens)
        if not self.phrase_override_labels:
            return [None] * n

        mask: List[Optional[str]] = [None] * n
        prio_index = {lab: i for i, lab in enumerate(self.priority)}

        # Walk labels in priority order so earlier ones win when phrases overlap
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
                        # Apply the override label across the whole phrase window
                        for k in range(i, i+m):
                            if mask[k] is None:
                                mask[k] = label
                        # do not skip ahead; allow overlaps but earlier labels already win
        return mask


    def label_token(self, tok: Token) -> Optional[str]:
        """
        Determine a single label for this token or None.
        Apply conflicts priority if multiple labels would match.
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


# -------------------------
# Fixed-schema verses + flexible tokens (by verse_id)
# -------------------------

def has_column(conn: sqlite3.Connection, table: str, col: str) -> bool:
    try:
        cur = conn.execute(f"PRAGMA table_info({table})")
        cols = [r[1].lower() for r in cur.fetchall()]
        return col.lower() in cols
    except Exception:
        return False


def detect_schema(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Fixed normalized schema for verses/books/chapters and flexible probe for tokens.
    Required tables:
      - books(id, book_name)
      - chapters(id, book_id, chapter_number)
      - verses(id, book_id, chapter_id, verse_num, text_plain)
    Tokens:
      Prefer 'tokens_with_lexicon' if present; else 'tokens_visible'; else 'tokens'.
      Must include: verse_id, token_idx, text; optional: strongs fields and lemma.
    """
    schema: Dict[str, Any] = {}
    # Fixed mapping for verses
    schema['verses'] = dict(table='verses',
                            id='id', book_id='book_id', chapter_id='chapter_id',
                            verse='verse_num', text='text_plain')

    # Decide token table
    def t_exists(name: str) -> bool:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name=?", (name,))
        return cur.fetchone() is not None

    token_table = None
    for cand in ['tokens_with_lexicon', 'vw_tokens_with_lexicon', 'tokens_visible', 'tokens']:
        if t_exists(cand):
            token_table = cand
            break
    if not token_table:
        raise RuntimeError("Could not find a token table/view (expected tokens_with_lexicon/tokens_visible/tokens).")

    # Probe columns
    def get_cols(t: str) -> List[str]:
        cur = conn.execute(f"PRAGMA table_info({t})")
        return [r[1] for r in cur.fetchall()]

    tcols = set(get_cols(token_table))

    # Required columns
    verse_id_col = 'verse_id' if 'verse_id' in tcols else None
    if not verse_id_col:
        raise RuntimeError(f"Token table {token_table} lacks verse_id column (found: {sorted(tcols)})")

    token_idx_col = None
    for c in ['token_idx', 'token_index', 'idx', 'ord']:
        if c in tcols:
            token_idx_col = c
            break
    if not token_idx_col:
        raise RuntimeError(f"Token table {token_table} lacks token order column (expected one of token_idx/token_index/idx/ord)")

    text_col = None
    for c in ['text', 'surface', 'token_text']:
        if c in tcols:
            text_col = c
            break
    if not text_col:
        raise RuntimeError(f"Token table {token_table} missing token text column (expected text/surface/token_text)")

    # Optional enrichments
    strongs_col = None
    for c in ['strong_norm', 'strongs', 'strongs_id', 's_strongs', 'strong_raw', 'strongsid']:
        if c in tcols:
            strongs_col = c
            break
    lemma_col = None
    for c in ['lemma', 'lex_lemma', 'base_lemma']:
        if c in tcols:
            lemma_col = c
            break
    pos_col = None
    for c in ['pos', 'upos', 'xpos', 'tag']:
        if c in tcols:
            pos_col = c
            break

    schema['tokens'] = dict(table=token_table,
                            verse_id=verse_id_col,
                            token_idx=token_idx_col,
                            text=text_col,
                            strongs=strongs_col, lemma=lemma_col, pos=pos_col,
                            source=('with_lexicon' if 'lexicon' in token_table else
                                    'visible' if 'visible' in token_table else 'tokens'))
    return schema


def fetch_verses(conn: sqlite3.Connection, s: Dict[str, Any], text_sql: str) -> List[Verse]:
    """Fixed-schema fetch:
    verses.id (verse_id), books.book_name, chapters.chapter_number, verses.verse_num, verses.text_plain
    """
    sql = f'''
        SELECT v.id AS verse_id,
               b.book_name AS book,
               c.chapter_number AS chapter,
               v.verse_num AS verse,
               {text_sql} AS text
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b    ON v.book_id = b.id
        ORDER BY b.index_number, c.chapter_number, v.verse_num
    '''
    cur = conn.execute(sql)
    rows = cur.fetchall()
    verses: List[Verse] = []
    for row in rows:
        verse_id = int(row["verse_id"]) if row["verse_id"] is not None else -1
        book = str(row["book"]) if row["book"] is not None else "UNKNOWN"
        chap = int(row["chapter"]) if row["chapter"] is not None else 0
        ver = int(row["verse"]) if row["verse"] is not None else 0
        text = row["text"] or ""
        verses.append(Verse(verse_id=verse_id, book=book, chapter=chap, verse=ver, text=text, tokens=[], align_spans=[]))
    return verses


def attach_tokens(conn: sqlite3.Connection, verses: List[Verse], s: Dict[str, Any]) -> None:
    """Attach tokens to verses by verse_id, ordering by token_idx."""
    tt = s['tokens']['table']
    cs = s['tokens']

    sql = f"""
        SELECT {cs['verse_id']} AS verse_id,
               {cs['token_idx']} AS tok_ord,
               {cs['text']} AS surface,
               {cs['strongs'] if cs['strongs'] else 'NULL'} AS strongs,
               {cs['lemma'] if cs['lemma'] else 'NULL'} AS lemma,
               {cs['pos'] if cs['pos'] else 'NULL'} AS pos
        FROM {tt}
        WHERE TRIM(COALESCE({cs['text']}, '')) <> ''
        ORDER BY verse_id, tok_ord
    """
    cur = conn.execute(sql)
    all_tok_rows = cur.fetchall()

    verse_index: Dict[int, Verse] = {v.verse_id: v for v in verses}

    attached = 0
    skipped = 0
    for row in all_tok_rows:
        verse_id, _ord, surface, strongs, lemma, pos = row
        if verse_id is None or surface is None:
            skipped += 1
            continue
        v = verse_index.get(int(verse_id))
        if v is None:
            skipped += 1
            continue
        tok = Token(surface=str(surface),
                    strongs_id=str(strongs) if strongs else None,
                    lemma=str(lemma) if lemma else None,
                    pos=str(pos) if pos else None)
        v.tokens.append(tok)
        attached += 1

    if skipped:
        print(f"WARN: Skipped {skipped} tokens due to missing verse_id or surface.", file=sys.stderr)
    print(f"INFO: Attached {attached} tokens (greedy alignment will compute spans).", file=sys.stderr)


# -------------------------
# Greedy alignment of token surfaces -> verses.text_plain
# -------------------------
def greedy_align_tokens_to_text(verse_text: str, token_surfaces: List[str]) -> Tuple[List[Tuple[int, int]], int]:
    """
    Left-to-right greedy alignment.
    For each token surface, find its next occurrence in verse_text starting at a moving cursor.
    Returns:
      - list of (start,end) for each token (or (-1,-1) if not found),
      - number of misses
    """
    spans: List[Tuple[int, int]] = []
    cursor = 0
    misses = 0

    for surf in token_surfaces:
        if not surf:
            spans.append((-1, -1))
            misses += 1
            continue

        # Direct find from current cursor
        idx = verse_text.find(surf, cursor)

        # Light normalization fallback: collapse consecutive spaces in the search window if needed
        if idx == -1 and "  " in verse_text[cursor: cursor + 200]:
            # Try a small sliding window search using relaxed matching (simple heuristic)
            # We won't modify spans beyond exact matches; this is just a second attempt.
            idx = verse_text.find(surf.replace("  ", " "), cursor)

        if idx == -1:
            spans.append((-1, -1))
            misses += 1
            # don't move cursor (we still try to align subsequent tokens)
        else:
            start = idx
            end = idx + len(surf)
            spans.append((start, end))
            cursor = end  # advance cursor to end of this match

    return spans, misses


# -------------------------
# Labeling & span construction
# -------------------------
def build_spans(verse: Verse, rules: LabelRules) -> List[Span]:
    spans: List[Span] = []

    # Greedy alignment once per verse (for all tokens)
    token_surfs = [t.surface for t in verse.tokens]
    align_spans, misses = greedy_align_tokens_to_text(verse.text, token_surfs)
    verse.align_spans = align_spans  # store for diagnostics

    # Label per token using rules; use aligned coords
    labeled: List[Tuple[int, int, str]] = []
    for t, (start, end) in zip(verse.tokens, align_spans):
        if start < 0 or end <= start:
            continue  # skip unaligned tokens
        lab = rules.label_token(t)
        if not lab:
            continue
        labeled.append((start, end, lab))

    if not labeled:
        return spans

    # Sort by start, then end
    labeled.sort(key=lambda x: (x[0], x[1]))

    if not rules.contiguous_merge:
        return [Span(start=a, end=b, label=lab) for (a, b, lab) in labeled]

    # Merge contiguous with same label
    cur_start, cur_end, cur_label = labeled[0]
    for i in range(1, len(labeled)):
        s, e, lab = labeled[i]
        if lab == cur_label and s == cur_end:  # contiguous
            cur_end = e
        else:
            spans.append(Span(start=cur_start, end=cur_end, label=cur_label))
            cur_start, cur_end, cur_label = s, e, lab
    spans.append(Span(start=cur_start, end=cur_end, label=cur_label))
    return spans


# -------------------------
# Stratified split & writer
# -------------------------
def stratified_split(
    items: List[Dict[str, Any]],
    by_key: str,
    ratios: Tuple[float, float, float],
    seed: int = 13,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Stratify by a key (e.g., 'book'). For each stratum, shuffle and split by ratios, then concat.
    """
    rng = random.Random(seed)
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for it in items:
        buckets[str(it.get(by_key, "UNKNOWN"))].append(it)

    train, dev, test = [], [], []
    r_train, r_dev, r_test = ratios

    for _k, group in buckets.items():
        rng.shuffle(group)
        n = len(group)
        n_train = int(round(r_train * n))
        n_dev = int(round(r_dev * n))
        n_test = max(0, n - n_train - n_dev)
        assigned = n_train + n_dev + n_test
        if assigned < n:
            n_test += (n - assigned)
        elif assigned > n:
            n_test = max(0, n - n_train - n_dev)

        train.extend(group[:n_train])
        dev.extend(group[n_train:n_train + n_dev])
        test.extend(group[n_train + n_dev: n_train + n_dev + n_test])

    return train, dev, test


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# -------------------------
# Main
# -------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Export silver NER dataset from concordance.db (greedy alignment)")
    parser.add_argument("--text_prefer", type=str, choices=["auto","clean","plain"], default="auto",
                        help="Which verse text to use: auto=COALESCE(text_clean,text_plain), clean=prefer text_clean (fallback plain if missing column), plain=text_plain only")
    default_db = "C:\\BIBLE\\concordance.db" if platform.system().lower().startswith("win") else "./concordance.db"
    parser.add_argument("--db", type=str, default=default_db, help="Path to concordance.db")
    parser.add_argument("--rules", type=str, required=True, help="Path to label_rules.yml")
    parser.add_argument("--outdir", type=str, default="./silver_out", help="Output directory for JSONL files")
    parser.add_argument("--seed", type=int, default=13, help="Random seed for shuffling")
    parser.add_argument("--ratios", type=float, nargs=3, default=(0.8, 0.1, 0.1),
                        help="Train/dev/test ratios (sum≈1.0)")
    parser.add_argument("--holdout_books", type=str, default="",
                        help='Comma-separated book names to also emit as a holdout file (e.g., "Matthew,Mark,Luke,John")')
    parser.add_argument("--holdout_name", type=str, default="domain_holdout",
                        help="Filename stem for the holdout JSONL (without extension)")
    parser.add_argument("--align_report", action="store_true",
                        help="Print alignment summary (miss counts) for first 50 verses per book.")
    parser.add_argument("--require_clean", action="store_true",
                        help="Strict guard: abort if verses.text_clean is missing or any verse has NULL/empty text_clean.")
    # NEW: optional fallback labeling for unmatched tokens
    parser.add_argument("--label-on-miss", type=str, default=None,
                        help='Assign this label to tokens that match no rule (e.g., "OTHER"). '
                             'Use "NONE" (or omit this flag) to disable fallback.')
    args = parser.parse_args()

    # Load rules
    with open(args.rules, "r", encoding="utf-8") as f:
        rules_cfg = yaml.safe_load(f)

    # Option B: read fallback label from YAML defaults
    label_on_miss = None
    try:
        _defaults = rules_cfg.get('defaults', {}) if isinstance(rules_cfg, dict) else {}
        if isinstance(_defaults, dict):
            label_on_miss = _defaults.get('label_on_miss')
            if label_on_miss is not None and not isinstance(label_on_miss, str):
                label_on_miss = str(label_on_miss)
    except Exception:
        label_on_miss = None

    # NEW: CLI override takes precedence over YAML
    if args.label_on_miss is not None:
        if args.label_on_miss.strip().upper() == "NONE":
            label_on_miss = None
        else:
            label_on_miss = args.label_on_miss.strip()

    rules = LabelRules(rules_cfg, label_on_miss=label_on_miss)

    # Optional: print the resolved fallback behavior
    if label_on_miss:
        print(f'INFO: Unmatched tokens will fall back to label "{label_on_miss}".', file=sys.stderr)
    else:
        print('INFO: No fallback label on miss (unmatched tokens remain unlabeled).', file=sys.stderr)

    # Sanity ratios
    r_train, r_dev, r_test = args.ratios
    ssum = r_train + r_dev + r_test
    if ssum <= 0:
        print("ERROR: Ratios must be positive.", file=sys.stderr)
        sys.exit(2)

    # Connect DB + detect schema
    if not os.path.exists(args.db):
        print(f"ERROR: DB not found at {args.db}", file=sys.stderr)
        sys.exit(2)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    try:
        schema = detect_schema(conn)
        print(f"INFO: Using verse table verses and token source {schema['tokens']['table']} ({schema['tokens']['source']}).",
              file=sys.stderr)

        # Decide verse text source
        use_clean_col = has_column(conn, 'verses', 'text_clean')
        if args.text_prefer == 'plain':
            text_sql = 'v.text_plain'
            print('INFO: text_prefer=plain → using verses.text_plain', file=sys.stderr)
        elif args.text_prefer == 'clean':
            if use_clean_col:
                text_sql = 'v.text_clean'
                print('INFO: text_prefer=clean → using verses.text_clean', file=sys.stderr)
            else:
                text_sql = 'v.text_plain'
                print('WARN: verses.text_clean not found; falling back to verses.text_plain', file=sys.stderr)
        else:  # auto
            if use_clean_col:
                text_sql = 'COALESCE(v.text_clean, v.text_plain)'
                print('INFO: text_prefer=auto → using COALESCE(text_clean,text_plain)', file=sys.stderr)
            else:
                text_sql = 'v.text_plain'
                print('INFO: text_prefer=auto but verses.text_clean missing → using verses.text_plain', file=sys.stderr)

        # Strict clean guard
        if args.require_clean:
            if not use_clean_col:
                print('ERROR: --require_clean set but verses.text_clean column not found.', file=sys.stderr)
                sys.exit(2)
            cur = conn.execute("SELECT COUNT(*) FROM verses WHERE text_clean IS NULL OR TRIM(text_clean) = ''")
            missing = int(cur.fetchone()[0])
            if missing > 0:
                print(f'ERROR: strict-clean guard: {missing} verses have NULL/empty text_clean. Fix clean step and rerun.', file=sys.stderr)
                sys.exit(2)
            else:
                print('INFO: strict-clean guard passed: all verses have non-empty text_clean.', file=sys.stderr)

        verses = fetch_verses(conn, schema, text_sql)
        attach_tokens(conn, verses, schema)

        # Build examples
        examples: List[Dict[str, Any]] = []
        holdout_books = {b.strip() for b in args.holdout_books.split(",") if b.strip()}
        holdout_rows: List[Dict[str, Any]] = []

        total_spans = 0
        with_spans = 0
        total_tokens = 0
        total_misses = 0

        # Optional per-book limited report
        report_budget_per_book = 50 if args.align_report else 0
        reported_per_book: Dict[str, int] = defaultdict(int)

        for v in verses:
            # Greedy align and label
            token_surfs = [t.surface for t in v.tokens]
            align_spans, misses = greedy_align_tokens_to_text(v.text, token_surfs)
            v.align_spans = align_spans

            # collect alignment stats
            total_tokens += len(token_surfs)
            total_misses += misses

            # ---------------------------
            # Initial per-token labels (Strong's / lemmas / single-token gazetteers)
            # ---------------------------
            token_labels: List[Optional[str]] = [None] * len(v.tokens)
            for idx, (t, (start, end)) in enumerate(zip(v.tokens, align_spans)):
                if start < 0 or end <= start:
                    continue
                token_labels[idx] = rules.label_token(t)

            # ---------------------------
            # Phrase pass: overlay phrase labels using conflicts.priority to break ties
            # ---------------------------
            phrase_labels = rules.phrase_labels_for_tokens(v.tokens)
            if phrase_labels:
                prio_index = {lab: i for i, lab in enumerate(rules.priority)}
                for i in range(len(v.tokens)):
                    plab = phrase_labels[i]
                    if not plab:
                        continue
                    cur = token_labels[i]
                    if cur is None:
                        token_labels[i] = plab
                    else:
                        # keep higher-priority label (lower index wins)
                        if prio_index.get(plab, 10**9) < prio_index.get(cur, 10**9):
                            token_labels[i] = plab
            
            # ---------------------------
            # Phrase OVERRIDE pass: make selected phrase labels 'sticky' across their window
            # ---------------------------
            override_mask = rules.phrase_override_mask(v.tokens)
            for i, olab in enumerate(override_mask):
                if olab:
                    token_labels[i] = olab

            # ---------------------------
            # Build labeled spans from final token_labels
            # ---------------------------
            labeled: List[Span] = []
            for (start, end), lab in zip(align_spans, token_labels):
                if lab and start >= 0 and end > start:
                    labeled.append(Span(start=start, end=end, label=lab))

            # Merge contiguous with same label if enabled (unchanged)
            if labeled:
                labeled.sort(key=lambda s: (s.start, s.end))
                if rules.contiguous_merge:
                    merged: List[Span] = []
                    cur = labeled[0]
                    for s in labeled[1:]:
                        if s.label == cur.label and v.text[cur.end:s.start].strip() == "":
                            cur = Span(start=cur.start, end=s.end, label=cur.label)
                        else:
                            merged.append(cur)
                            cur = s
                    merged.append(cur)
                    spans = merged
                else:
                    spans = labeled
            else:
                spans = []

            total_spans += len(spans)
            if spans:
                with_spans += 1

            row = {
                "id": f"{v.book}|{v.chapter}:{v.verse}",  # stable unique key for dedupe
                "book": v.book,
                "chapter": v.chapter,
                "verse": v.verse,
                "text": v.text,
                "spans": [{"start": s.start, "end": s.end, "label": s.label} for s in spans],
                "meta": {"ref": f"{v.book} {v.chapter}:{v.verse}"},  # nice display in Prodigy
            }


            # Optional alignment mini-report
            if report_budget_per_book and reported_per_book[v.book] < report_budget_per_book:
                reported_per_book[v.book] += 1
                aligned_cnt = len(token_surfs) - misses
                print(
                    f"ALIGN [{v.book} {v.chapter}:{v.verse}] tokens={len(token_surfs)} "
                    f"aligned={aligned_cnt} misses={misses}",
                    file=sys.stderr,
                )

            if v.book in holdout_books:
                holdout_rows.append(row)
            else:
                examples.append(row)

        # Final alignment summary
        pass_rate = 0.0 if total_tokens == 0 else (total_tokens - total_misses) / total_tokens
        print(f"INFO: Greedy alignment pass rate: {pass_rate:.4%} "
              f"({total_tokens - total_misses}/{total_tokens} token surfaces matched).", file=sys.stderr)

        print(f"INFO: Built {len(examples)} examples (+ {len(holdout_rows)} in holdout set).", file=sys.stderr)
        print(f"INFO: Total labeled spans: {total_spans}; verses with ≥1 span: {with_spans}.", file=sys.stderr)

        # Ensure deterministic ordering before we split/write
        examples.sort(key=lambda r: (str(r["book"]), int(r["chapter"]), int(r["verse"])))
        holdout_rows.sort(key=lambda r: (str(r["book"]), int(r["chapter"]), int(r["verse"])))

        # Split stratified by book
        train_rows, dev_rows, test_rows = stratified_split(
            items=examples, by_key="book",
            ratios=(r_train / ssum, r_dev / ssum, r_test / ssum), seed=args.seed
        )

        # Write files
        outdir = args.outdir
        write_jsonl(os.path.join(outdir, "train.jsonl"), train_rows)
        write_jsonl(os.path.join(outdir, "dev.jsonl"), dev_rows)
        write_jsonl(os.path.join(outdir, "test.jsonl"), test_rows)

        if holdout_rows:
            write_jsonl(os.path.join(outdir, f"{args.holdout_name}.jsonl"), holdout_rows)

        print(f"INFO: Wrote dataset to {outdir}", file=sys.stderr)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
