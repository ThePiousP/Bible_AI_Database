
from typing import Dict, Any, List, Optional
import json

try:
    import spacy
    from spacy.tokens import Span
except Exception:  # pragma: no cover
    spacy = None
    Span = None

# 1) Define a Span extension for alternate labels (idempotent)
def ensure_span_extension():
    if Span is None:
        return
    if not Span.has_extension("alt_labels"):
        Span.set_extension("alt_labels", default=None)

# 2) Build a lookup from a DEITY gazetteer that has optional "also_labels" + "where"
def load_multilabel_lookup(path: str) -> Dict[str, Dict[str, Any]]:
    """
    Returns a dict mapping entry text -> {"also_labels": [...], "where": {...}, "note": ...}
    - Keys are stored in both exact form and a lower-cased normalization to improve matching.
    - If the JSON has top-level {"DEITY": {...}}, we flatten from there.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    block = data.get("DEITY", data)  # allow either nested or flat
    lookup: Dict[str, Dict[str, Any]] = {}
    for entry_text, payload in block.items():
        if not isinstance(payload, dict):
            continue
        also = payload.get("also_labels")
        where = payload.get("where")
        note = payload.get("note")
        record = {}
        if also:
            record["also_labels"] = also
        if where:
            record["where"] = where
        if note is not None:
            record["note"] = note
        if record:
            # store under exact and normalized keys
            lookup[entry_text] = record
            lookup.setdefault(entry_text.lower(), record)
    return lookup

def _matches_where(verse_uid: Optional[str], text: str, where: Dict[str, Any]) -> bool:
    if not where:
        return True
    # verse_uid filter
    allowed = where.get("verse_uid")
    if allowed:
        # normalize any incoming verse uid (e.g., trims, case-insensitivity)
        v = (verse_uid or "").strip()
        if v and v not in allowed:
            return False
    # text_contains_any filter
    needles: List[str] = where.get("text_contains_any") or []
    if needles:
        t = text  # keep case sensitivity; this is intentional to respect KJV casing rules
        found = any(n in t for n in needles)
        if not found:
            return False
    return True

# 3) Apply alt labels onto spans in a doc
def apply_alt_labels(doc, verse_uid: Optional[str], lookup: Dict[str, Dict[str, Any]]):
    """
    For each span in doc.ents, if its text is in the lookup and the `where` matches,
    set span._.alt_labels = also_labels (list). This does not change span.label_.
    """
    ensure_span_extension()
    if not lookup or not getattr(doc, "ents", None):
        return doc

    # Optional: capture full verse text for simple "text_contains_any" checks
    text = doc.text

    for span in list(doc.ents):
        key_exact = span.text
        key_norm = span.text.lower()
        meta = lookup.get(key_exact) or lookup.get(key_norm)
        if not meta:
            continue
        also = meta.get("also_labels")
        where = meta.get("where")
        if not also:
            continue
        if _matches_where(verse_uid, text, where or {}):
            # Assign alt labels; preserve if already present
            if span._.alt_labels is None:
                span._.alt_labels = list(dict.fromkeys(also))  # de-dupe, preserve order
            else:
                # merge
                merged = list(dict.fromkeys(list(span._.alt_labels) + list(also)))
                span._.alt_labels = merged
    return doc
