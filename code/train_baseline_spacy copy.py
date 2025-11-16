# train_baseline_spacy.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Train a quick spaCy NER baseline from the silver JSONL produced by export_ner_silver.py.

The script:
  - Loads train/dev/test JSONL with fields: book, chapter, verse, text, spans[{start,end,label}]
  - Creates spaCy Docs and gold spans via char offsets.
  - Initializes a lightweight 'en' pipeline with tok2vec + ner.
  - Trains for a small number of epochs (configurable).
  - Saves the best model and prints evaluation on the test set.

Usage:
  pip install spacy
  python -m spacy download en_core_web_sm   # or skip model download and use blank("en")

  python train_baseline_spacy.py --data ./silver_out --output ./models/spacy_silver_v1 --epochs 20
"""
from __future__ import annotations

import argparse
import json
import os
import random
from typing import List, Dict, Any, Tuple

import spacy
from spacy.tokens import DocBin, Doc
from spacy.training.example import Example


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def make_docs(nlp, rows: List[Dict[str, Any]], labels: List[str], warn_dropout: bool = True) -> Tuple[List[Doc], int]:
    docs = []
    skipped_spans = 0
    for r in rows:
        text = r["text"]
        spans = r.get("spans", [])
        doc = nlp.make_doc(text)
        ents = []
        for sp in spans:
            start, end, label = sp["start"], sp["end"], sp["label"]
            if label not in labels:
                # Skip unknown labels silently
                continue
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span is None:
                skipped_spans += 1
                continue
            ents.append(span)
        doc.ents = spacy.util.filter_spans(ents)  # handle overlaps
        docs.append(doc)
    return docs, skipped_spans


def evaluate(nlp, rows: List[Dict[str, Any]], labels: List[str]) -> Dict[str, Any]:
    examples = []
    for r in rows:
        text = r["text"]
        spans = r.get("spans", [])
        doc = nlp.make_doc(text)
        ents = []
        for sp in spans:
            start, end, label = sp["start"], sp["end"], sp["label"]
            if label not in labels:
                continue
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span is None:
                continue
            ents.append(span)
        gold = Doc(doc.vocab, words=[t.text for t in doc], spaces=[bool(t.whitespace_) for t in doc])
        gold.ents = ents
        examples.append(Example.from_dict(doc, {"entities": [(e.start_char, e.end_char, e.label_) for e in ents]}))
    return nlp.evaluate(examples)


def main():
    parser = argparse.ArgumentParser(description="Train a spaCy NER baseline from silver dataset")
    parser.add_argument("--data", type=str, default="./silver_out", help="Directory with train/dev/test jsonl")
    parser.add_argument("--output", type=str, default="./models/spacy_silver_v1", help="Output model directory")
    parser.add_argument("--lang", type=str, default="en", help="Language code (default: en)")
    parser.add_argument("--epochs", type=int, default=20, help="Training epochs")
    parser.add_argument("--batch_size", type=int, default=128, help="Batch size")
    parser.add_argument("--seed", type=int, default=13, help="Random seed")
    parser.add_argument("--labels", type=str, nargs="+", default=["DEITY", "PERSON", "PLACE"],
                        help="Labels to train/evaluate")
    parser.add_argument("--use_pretrained", action="store_true",
                        help="If set, try to use en_core_web_sm; otherwise use blank pipeline.")
    args = parser.parse_args()

    random.seed(args.seed)
    os.makedirs(args.output, exist_ok=True)

    train_path = os.path.join(args.data, "train.jsonl")
    dev_path = os.path.join(args.data, "dev.jsonl")
    test_path = os.path.join(args.data, "test.jsonl")
    for p in [train_path, dev_path, test_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing dataset file: {p}")

    train_rows = load_jsonl(train_path)
    dev_rows = load_jsonl(dev_path)
    test_rows = load_jsonl(test_path)

    # Initialize pipeline
    if args.use_pretrained:
        try:
            nlp = spacy.load("en_core_web_sm")
        except Exception:
            print("WARN: en_core_web_sm not available; falling back to blank('en').")
            nlp = spacy.blank(args.lang)
    else:
        nlp = spacy.blank(args.lang)

    if "tok2vec" not in nlp.pipe_names:
        tok2vec = nlp.add_pipe("tok2vec")
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")

    # Register labels
    for lab in args.labels:
        ner.add_label(lab)

    # Build docs
    train_docs, skipped_train = make_docs(nlp, train_rows, labels=args.labels)
    dev_docs, skipped_dev = make_docs(nlp, dev_rows, labels=args.labels)
    print(f"Prepared {len(train_docs)} train docs (skipped {skipped_train} spans), "
          f"{len(dev_docs)} dev docs (skipped {skipped_dev} spans).")

    # Convert to DocBin for efficient training
    db_train = DocBin(store_user_data=False)
    for d in train_docs:
        db_train.add(d)
    db_dev = DocBin(store_user_data=False)
    for d in dev_docs:
        db_dev.add(d)

    train_examples = [Example.from_dict(nlp.make_doc(d.text), {"entities": [(e.start_char, e.end_char, e.label_) for e in d.ents]})
                      for d in train_docs]
    dev_examples = [Example.from_dict(nlp.make_doc(d.text), {"entities": [(e.start_char, e.end_char, e.label_) for e in d.ents]})
                    for d in dev_docs]

    # Train
    nlp.initialize(get_examples=lambda: train_examples)
    optimizer = nlp.resume_training()
    best_score = -1.0
    best_path = os.path.join(args.output, "best")

    for epoch in range(args.epochs):
        random.shuffle(train_examples)
        losses = {}
        batches = spacy.util.minibatch(train_examples, size=args.batch_size)
        for batch in batches:
            nlp.update(batch, sgd=optimizer, losses=losses, drop=0.1)
        # Evaluate on dev
        dev_score = nlp.evaluate(dev_examples)["ents_f"]
        print(f"Epoch {epoch+1}/{args.epochs} - Losses: {losses} - Dev F1: {dev_score:.4f}")
        if dev_score > best_score:
            best_score = dev_score
            nlp.to_disk(best_path)

    print(f"Training complete. Best dev F1: {best_score:.4f}. Model saved to {best_path}")

    # Final evaluation on test
    nlp = spacy.load(best_path)
    test_metrics = evaluate(nlp, test_rows, labels=args.labels)
    print("Test metrics (overall):")
    print({k: float(v) if isinstance(v, (int, float)) else v for k, v in test_metrics.items()})
    # Per-entity scores are inside test_metrics["ents_per_type"] if available
    per_type = test_metrics.get("ents_per_type", {})
    if per_type:
        print("Per-label metrics:")
        for lab, scores in per_type.items():
            print(lab, {k: float(v) for k, v in scores.items()})
    # Save final model copy
    final_path = os.path.join(args.output, "final")
    nlp.to_disk(final_path)
    print(f"Final model saved to {final_path}")


if __name__ == "__main__":
    main()
