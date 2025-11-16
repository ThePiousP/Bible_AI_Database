
from typing import Iterable, Dict, List, Tuple, Optional

try:
    from spacy.tokens import Doc, Span
except Exception:  # pragma: no cover
    Doc = None
    Span = None

Record = Dict[str, object]

def _span_to_record(span: "Span", verse_uid: Optional[str], label: Optional[str] = None) -> Record:
    return {
        "verse_uid": verse_uid,
        "start_char": int(span.start_char),
        "end_char": int(span.end_char),
        "label": label if label is not None else span.label_,
        "text": span.text,
    }

def iter_doc_ents_with_altlabels(doc: "Doc", verse_uid: Optional[str], allowed_alt: Optional[Iterable[str]] = None) -> List[Record]:
    """
    Produce records for all base entities plus duplicates for any alt labels.
    - allowed_alt: if provided, only duplicate for labels in this set (e.g., {"LOCATION"}).
    """
    if doc is None or not getattr(doc, "ents", None):
        return []

    out: List[Record] = []
    seen: set = set()

    for span in doc.ents:
        # base record
        rec = _span_to_record(span, verse_uid, label=span.label_)
        key = (rec["start_char"], rec["end_char"], rec["label"])
        if key not in seen:
            out.append(rec)
            seen.add(key)

        # alt labels (if any)
        alt = getattr(span._, "alt_labels", None)
        if alt:
            for lab in alt:
                if allowed_alt is not None and lab not in set(allowed_alt):
                    continue
                rec_alt = _span_to_record(span, verse_uid, label=lab)
                key_alt = (rec_alt["start_char"], rec_alt["end_char"], rec_alt["label"])
                if key_alt not in seen:
                    out.append(rec_alt)
                    seen.add(key_alt)

    return out
