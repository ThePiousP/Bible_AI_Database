#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dataset_audit.py — Quick QA for the silver JSONL dataset.

What it does:
  • Loads train/dev/test JSONL
  • Validates that every span slices cleanly into the verse text
  • Prints label histograms (per split + global)
  • Prints per-book label coverage (how many verses have >=1 span per label)
  • Shows a few random examples per label for spot-checks

Usage:
  python dataset_audit.py --data ./silver_out --samples-per-label 5
"""

from __future__ import annotations
import argparse, json, os, random
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def validate_spans(rows: List[Dict[str, Any]]) -> Tuple[int,int,int]:
    """Return (total_spans, ok_spans, bad_spans)."""
    total=ok=bad=0
    for r in rows:
        text = r.get("text","")
        for sp in r.get("spans",[]):
            total += 1
            s, e = sp["start"], sp["end"]
            if 0 <= s < e <= len(text):
                ok += 1
            else:
                bad += 1
    return total, ok, bad

def label_hist(rows: List[Dict[str, Any]]) -> Counter:
    c = Counter()
    for r in rows:
        for sp in r.get("spans",[]):
            c[sp["label"]] += 1
    return c

def verses_with_label(rows: List[Dict[str, Any]]) -> Counter:
    c = Counter()
    for r in rows:
        labs = {sp["label"] for sp in r.get("spans",[])}
        for lab in labs:
            c[lab]+=1
    return c

def per_book_coverage(rows: List[Dict[str, Any]]) -> Dict[str, Counter]:
    d = defaultdict(Counter)
    for r in rows:
        book = str(r.get("book","UNKNOWN"))
        labs = {sp["label"] for sp in r.get("spans",[])}
        for lab in labs:
            d[book][lab]+=1
    return d

def sample_examples(rows: List[Dict[str, Any]], per_label: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    buckets = defaultdict(list)
    for r in rows:
        for sp in r.get("spans",[]):
            buckets[sp["label"]].append((r, sp))
    out = {}
    for lab, items in buckets.items():
        random.shuffle(items)
        picks = []
        for (r, sp) in items[:per_label]:
            snippet = r["text"][sp["start"]:sp["end"]]
            picks.append({
                "ref": f'{r["book"]} {r["chapter"]}:{r["verse"]}',
                "label": sp["label"],
                "span_text": snippet,
                "text": r["text"]
            })
        out[lab]=picks
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="./silver_out", help="Dir with train/dev/test.jsonl")
    ap.add_argument("--samples-per-label", type=int, default=5)
    args = ap.parse_args()

    paths = {k: os.path.join(args.data, f"{k}.jsonl") for k in ("train","dev","test")}
    for p in paths.values():
        if not os.path.exists(p):
            raise FileNotFoundError(p)

    splits = {k: load_jsonl(p) for k,p in paths.items()}

    print("=== Span Integrity ===")
    for k, rows in splits.items():
        total, ok, bad = validate_spans(rows)
        print(f"{k}: spans={total}, ok={ok}, bad={bad}")

    print("\n=== Label Histogram (per split) ===")
    global_hist = Counter()
    global_vwl  = Counter()
    for k, rows in splits.items():
        hist = label_hist(rows)
        vwl  = verses_with_label(rows)
        global_hist += hist
        global_vwl  += vwl
        print(f"{k}:")
        for lab, n in hist.most_common():
            print(f"  {lab}: {n} (verses with >=1: {vwl[lab]})")

    print("\n=== Label Histogram (global) ===")
    for lab, n in global_hist.most_common():
        print(f"  {lab}: {n} (verses with >=1: {global_vwl[lab]})")

    print("\n=== Per-book coverage (verses with >=1 span, top 10 books by total) ===")
    per_book = per_book_coverage([*splits["train"], *splits["dev"], *splits["test"]])
    ranked = sorted(per_book.items(), key=lambda kv: sum(kv[1].values()), reverse=True)[:10]
    for book, cnt in ranked:
        counts = " | ".join(f"{lab}={cnt[lab]}" for lab in sorted(cnt))
        print(f"  {book}: {counts}")

    print("\n=== Random examples per label ===")
    ex = sample_examples([*splits["train"], *splits["dev"], *splits["test"]], args.samples_per_label)
    for lab, items in ex.items():
        print(f"[{lab}]")
        for it in items:
            print(f'  {it["ref"]}: “…{it["span_text"]}…”')

if __name__ == "__main__":
    main()
