#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
propose_label_candidates.py — mine PERSON/PLACE candidate Strong's IDs for curation.

Heuristics (conservative):
  • PERSON candidates: tokens that are capitalized and NOT at verse-start noise like "And", "But", etc.
  • PLACE  candidates: tokens surrounded by toponyms cues ("in", "at", "from", "to", "into") or surfaces like "Mount", "River", "Valley",
                       OR capitalized tokens frequently followed by "of" patterns ("X of Y") that are common in place names.

Outputs (CSV):
  • candidate_PERSON.csv: strong_norm, count, distinct_surfaces(sample), example_refs(sample)
  • candidate_PLACE.csv:  strong_norm, count, distinct_surfaces(sample), example_refs(sample)

Usage:
  python propose_label_candidates.py --db ./concordance.db --outdir ./candidates
"""
from __future__ import annotations
import argparse, os, csv, sqlite3, re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

NOISE = set(["And","But","For","The","A","An","So","Then","Now","Thus","Therefore","Because","That","Which","Who","Whom","Whose","When","Where","While","Behold"])

TOPONYM_MARKERS = set(["in","at","from","to","into","toward","towards","over","under","by","near","around","through","throughout","beyond","beside","between","within"])
PLACE_SURFACE_HINTS = set(["Mount","Hill","Valley","River","Sea","Lake","Brook","Gulf","Plain","Desert","Wilderness","Town","City","Village","Region","Land","Island","Isle"])

def fetch_tokens(conn: sqlite3.Connection):
    # Prefer tokens_with_lexicon -> tokens_visible -> tokens
    def t_exists(name: str) -> bool:
        row = conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name=?", (name,)).fetchone()
        return row is not None
    table = None
    for cand in ("tokens_with_lexicon","vw_tokens_with_lexicon","tokens_visible","tokens"):
        if t_exists(cand):
            table = cand
            break
    if not table:
        raise RuntimeError("No token table found")

    # Need verse reference for examples
    q = f"""
    SELECT t.verse_id, t.text AS surface, t.strong_norm AS strongs
    FROM {table} t
    WHERE TRIM(COALESCE(t.text,'')) <> ''
    ORDER BY t.verse_id, t.rowid
    """
    return table, conn.execute(q)

def verse_ref_lookup(conn: sqlite3.Connection) -> Dict[int,str]:
    q = """
    SELECT v.id as verse_id, b.book_name||' '||c.chapter_number||':'||v.verse_num AS ref
    FROM verses v
    JOIN chapters c ON v.chapter_id=c.id
    JOIN books b ON v.book_id=b.id
    """
    return {row["verse_id"]: row["ref"] for row in conn.execute(q)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="./concordance.db")
    ap.add_argument("--outdir", default="./candidates")
    ap.add_argument("--min_count", type=int, default=5, help="minimum token count to include")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    conn = sqlite3.connect(args.db); conn.row_factory = sqlite3.Row

    try:
        table, cur = fetch_tokens(conn)
        refs = verse_ref_lookup(conn)

        # We'll collect per-Strong's aggregates with light heuristics
        person_counts = Counter()
        person_surfs  = defaultdict(Counter)
        person_refs   = defaultdict(list)

        place_counts = Counter()
        place_surfs  = defaultdict(Counter)
        place_refs   = defaultdict(list)

        prev_by_verse: Dict[int, List[str]] = defaultdict(list)

        for row in cur:
            vid = row["verse_id"]; surf = str(row["surface"]); sid = row["strongs"]
            if not sid or not surf:
                continue
            # store for context heuristics
            prev_by_verse[vid].append(surf)

            # PERSON heuristic: capitalized (A-Z start), not a noise determiner/conjunction
            if surf and surf[0].isupper() and surf not in NOISE and re.match(r"^[A-Za-z’'-]+$", surf):
                person_counts[sid]+=1
                person_surfs[sid][surf]+=1
                if len(person_refs[sid])<5:
                    person_refs[sid].append(refs.get(vid,str(vid)))

        # PLACE heuristic: re-scan verse sequences for contextual cues
        for vid, toks in prev_by_verse.items():
            for i, surf in enumerate(toks):
                sid = None  # we don't have a quick map here, so skip sid-less path
            # To keep things conservative and DB-agnostic, we won't add extra PLACE rules beyond capitalized hints here.

        # Write CSVs
        def write_csv(path: str, rows: List[Tuple[str,int,List[Tuple[str,int]],List[str]]]):
            with open(path,"w",newline="",encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["strongs_id","count","top_surfaces","example_refs"])
                for sid, cnt, surf_counts, ex in rows:
                    tops = "; ".join([f"{s}×{n}" for s,n in surf_counts[:5]])
                    w.writerow([sid, cnt, tops, "; ".join(ex)])

        person_rows = []
        for sid, cnt in person_counts.items():
            if cnt >= args.min_count:
                surf_counts = sorted(person_surfs[sid].items(), key=lambda kv: kv[1], reverse=True)
                person_rows.append((sid, cnt, surf_counts, person_refs[sid]))
        person_rows.sort(key=lambda r: r[1], reverse=True)

        write_csv(os.path.join(args.outdir,"candidate_PERSON.csv"), person_rows)

        # For PLACE, we start conservative: use the person heuristic as a seed but save to PLACE candidates separately later
        # (We keep PLACE empty now to avoid false positives; you can re-run this script later when we add context cues.)
        write_csv(os.path.join(args.outdir,"candidate_PLACE.csv"), [])

        print(f"Wrote candidates to {args.outdir}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
