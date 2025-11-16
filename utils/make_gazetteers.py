#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_gazetteers_from_curated.py
Converts curated JSONs (e.g., LOCATION.json with {CATEGORY: {text: {note..}}})
into flat .txt gazetteers (one entry per line) for use in label_rules.yml.

Usage:
  python make_gazetteers_from_curated.py --curated_dir ./bible_entities_curated_v2 --out ./gazetteers
"""

import argparse, json, os, pathlib, sys

CATS = [
    "DEITY","DIVINE_TITLE","TITLE","PERSON","LOCATION","BIBLE_NATIONS","TOOLS_MEASUREMENTS"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--curated_dir", default="./bible_entities")
    ap.add_argument("--out", default="./gazetteers")
    args = ap.parse_args()

    cur = pathlib.Path(args.curated_dir)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # map LOCATION->PLACE filename so it matches your label name
    rename = {"LOCATION": "PLACE"}

    written = []
    for cat in CATS:
        src = cur / f"{cat}.json"
        if not src.exists():
            # Some curated sets may name file by category group; we still try this name
            continue
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"WARN: could not read {src}: {e}", file=sys.stderr)
            continue

        # Expected shape: { cat: { "Entry": {...}, ... } }
        entries = []
        if isinstance(data, dict) and cat in data and isinstance(data[cat], dict):
            entries = sorted(list(data[cat].keys()), key=lambda s: (s.lower(), s))

        # Write flat gazetteer
        out_name = rename.get(cat, cat) + ".txt"
        out_path = out / out_name
        with out_path.open("w", encoding="utf-8") as f:
            for line in entries:
                if line.strip():
                    f.write(line.strip()+"\n")
        written.append(str(out_path))

    print("Wrote gazetteers:\n  " + "\n  ".join(written))

if __name__ == "__main__":
    main()
