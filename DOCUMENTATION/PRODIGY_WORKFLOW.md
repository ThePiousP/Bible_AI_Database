# Prodigy Annotation Workflow Guide

**Created**: 2025-11-16
**Version**: 1.0
**Phase**: NER Prodigy Annotation

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Configuration](#configuration)
4. [Annotation Workflows](#annotation-workflows)
5. [Quality Control](#quality-control)
6. [Export & Integration](#export--integration)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers the complete workflow for annotating biblical NER data using Prodigy. The project uses a **silver→gold** annotation strategy:

1. **Silver Dataset**: Auto-generated from Strong's numbers + gazetteers (`silver_out/`)
2. **Gold Dataset**: Human-validated annotations via Prodigy (`bible_gold`)
3. **Final Training**: Combine silver + gold for maximum performance

**Prodigy Resources**:
- Patterns File: `prodigy_patterns.jsonl` (2,833 patterns)
- Keymaps: `prodigy.json` (keyboard shortcuts for labels)
- Entity Taxonomy: 65 biblical entity types (see `label_rules.yml`)

---

## Prerequisites

### 1. Prodigy License

Prodigy is a commercial tool. You need a license from [https://prodi.gy](https://prodi.gy).

**Installation**:
```bash
pip install prodigy -f https://XXXX-XXXX-XXXX-XXXX@download.prodi.gy
```

Replace `XXXX-XXXX-XXXX-XXXX` with your license key.

**Verify installation**:
```bash
prodigy --help
```

---

### 2. Silver Dataset

Generate the silver dataset first:

```bash
cd /path/to/Bible_AI_Database

# Export silver dataset
python code/silver_export.py \
    --db data/GoodBook.db \
    --rules label_rules.yml \
    --outdir silver_out \
    --seed 13
```

Output:
- `silver_out/train.jsonl` (80% of data)
- `silver_out/dev.jsonl` (10% of data)
- `silver_out/test.jsonl` (10% of data)

---

### 3. Prodigy Database Setup

Initialize Prodigy database:

```bash
# Create empty dataset
prodigy dataset bible_gold "Gold-standard biblical NER annotations"

# Verify
prodigy db-in bible_gold
```

---

## Configuration

### Keyboard Shortcuts (prodigy.json)

The `prodigy.json` file defines keyboard shortcuts for fast annotation:

```json
{
  "keymap_by_label": {
    "DEITY": "d",
    "PERSON": "p",
    "LOCATION": "l",
    "TITLE": "t",
    "TIME": "5",
    "PROPHET": "9",
    "FALSE_GOD": "0",
    "BIBLE_NATIONS": "[",
    "BIBLE_ANIMALS": "]",
    "CONCEPT": "c",
    "SPIRITUAL_ENTITY": "e",
    "FOOD": "f",
    "VERB": "v",
    "OTHER": "?"
  }
}
```

**Usage in Prodigy**:
- Press **d** to tag selected text as DEITY
- Press **p** to tag as PERSON
- Press **l** to tag as LOCATION
- etc.

---

### Pattern File (prodigy_patterns.jsonl)

Contains 2,833 pre-defined entity patterns for:
- Persons (Moses, David, Abraham, etc.)
- Locations (Jerusalem, Egypt, Galilee, etc.)
- Divine titles (Lord of Hosts, Holy One of Israel, etc.)
- Time expressions (in the beginning, seventh day, etc.)
- And 61 more entity types

**Format**:
```jsonl
{"label": "PERSON", "pattern": "Moses"}
{"label": "PERSON", "pattern": "David"}
{"label": "LOCATION", "pattern": "Jerusalem"}
{"label": "DEITY", "pattern": "LORD"}
```

Patterns are loaded automatically in annotation recipes.

---

## Annotation Workflows

### Workflow 1: Manual Annotation (Recommended)

**Use case**: Maximum precision, complete control

**Command**:
```bash
prodigy ner.manual bible_gold blank:en ./silver_out/train.jsonl \
    --label DEITY,PERSON,LOCATION,TITLE,PROPHET,TIME,GROUP,EVENT \
    --patterns ./prodigy_patterns.jsonl
```

**Parameters**:
- `bible_gold`: Dataset name (will be created if not exists)
- `blank:en`: Blank English spaCy model (no pre-trained NER)
- `./silver_out/train.jsonl`: Input data
- `--label`: Entity types to annotate (comma-separated)
- `--patterns`: Pre-loaded patterns file

**Workflow**:
1. Prodigy displays verse text
2. Pre-loaded patterns automatically suggest entities
3. You review and correct suggestions
4. Accept/reject/modify annotations
5. Press **Accept** or **Reject** for each example

**Tips**:
- Start with high-priority labels (DEITY, PERSON, LOCATION)
- Add more labels incrementally
- Use keyboard shortcuts for speed (see prodigy.json)

---

### Workflow 2: Active Learning (ner.teach)

**Use case**: Faster annotation, model-assisted suggestions

**Command**:
```bash
prodigy ner.teach bible_gold en_core_web_lg ./silver_out/train.jsonl \
    --label DEITY,PERSON,LOCATION \
    --patterns ./prodigy_patterns.jsonl
```

**Parameters**:
- `en_core_web_lg`: Use pre-trained spaCy model for suggestions
- Model learns from your annotations in real-time
- Suggests examples where model is most uncertain

**Workflow**:
1. Model suggests entity spans
2. You accept/reject/correct
3. Model updates in background
4. Next suggestions are more accurate

**Pros**:
- Faster than manual annotation
- Model learns your preferences
- Adaptive to annotation style

**Cons**:
- May introduce model bias
- Less control over annotation order

---

### Workflow 3: Patterns-Only Review

**Use case**: Verify auto-generated patterns

**Command**:
```bash
prodigy ner.manual bible_gold blank:en ./silver_out/train.jsonl \
    --label DEITY,PERSON,LOCATION \
    --patterns ./prodigy_patterns.jsonl \
    --highlight-chars
```

**Purpose**: Review and correct pattern-based suggestions

---

### Workflow 4: Focused Book Annotation

**Use case**: Annotate specific books (e.g., Gospels)

**Preparation**:
```bash
# Export holdout books separately
python code/silver_export.py \
    --db data/GoodBook.db \
    --rules label_rules.yml \
    --outdir silver_out_gospels \
    --holdout-books Matthew Mark Luke John \
    --seed 13
```

**Annotate**:
```bash
prodigy ner.manual bible_gospels blank:en ./silver_out_gospels/train.jsonl \
    --label DEITY,PERSON,LOCATION,TITLE \
    --patterns ./prodigy_patterns.jsonl
```

---

## Quality Control

### 1. Dual Annotation

For high-quality gold data, have 2+ annotators annotate the same examples:

**Annotator 1**:
```bash
prodigy ner.manual bible_gold_ann1 blank:en ./sample_set.jsonl \
    --label DEITY,PERSON,LOCATION \
    --patterns ./prodigy_patterns.jsonl
```

**Annotator 2**:
```bash
prodigy ner.manual bible_gold_ann2 blank:en ./sample_set.jsonl \
    --label DEITY,PERSON,LOCATION \
    --patterns ./prodigy_patterns.jsonl
```

**Measure Agreement**:
```bash
# Export both datasets
prodigy db-out bible_gold_ann1 > ann1.jsonl
prodigy db-out bible_gold_ann2 > ann2.jsonl

# Calculate Inter-Annotator Agreement (IAA)
python scripts/annotation_quality.py --calculate-iaa ann1.jsonl ann2.jsonl
```

**Target IAA**: Cohen's Kappa ≥ 0.85 (excellent agreement)

---

### 2. Annotation Statistics

Track progress and quality:

```bash
# View dataset stats
prodigy stats bible_gold

# Count annotations by label
prodigy db-out bible_gold | python -c "
import sys, json
from collections import Counter
labels = []
for line in sys.stdin:
    obj = json.loads(line)
    for span in obj.get('spans', []):
        labels.append(span['label'])
print(Counter(labels).most_common())
"
```

---

### 3. Quality Checks

**Check for missing annotations**:
```bash
# Find verses with no entities tagged
prodigy db-out bible_gold | python -c "
import sys, json
for line in sys.stdin:
    obj = json.loads(line)
    if not obj.get('spans'):
        print(f\"{obj['meta']['book']} {obj['meta']['chapter']}:{obj['meta']['verse']}\")
"
```

**Check for label consistency**:
- Review entities tagged with multiple labels
- Ensure theological terms are consistently labeled
- Verify proper names vs. titles

---

## Export & Integration

### 1. Export Annotations

```bash
# Export to JSONL
prodigy db-out bible_gold > output/gold_annotations.jsonl

# Export to spaCy format
prodigy data-to-spacy output/spacy_data \
    --ner bible_gold \
    --eval-split 0.1
```

Output:
- `output/spacy_data/train.spacy`
- `output/spacy_data/dev.spacy`

---

### 2. Merge with Silver Dataset

Combine silver (auto-generated) + gold (human-annotated) for training:

```bash
# Merge datasets
cat silver_out/train.jsonl output/gold_annotations.jsonl > final_train.jsonl

# Or deduplicate first
python scripts/merge_datasets.py \
    --silver silver_out/train.jsonl \
    --gold output/gold_annotations.jsonl \
    --output final_train.jsonl \
    --deduplicate
```

---

### 3. Train NER Model

```bash
# Train spaCy model on combined data
python code/train_baseline_spacy.py \
    --train final_train.jsonl \
    --dev silver_out/dev.jsonl \
    --test silver_out/test.jsonl \
    --output models/ner_v2_gold \
    --epochs 30 \
    --batch-size 32
```

---

## Best Practices

### Annotation Guidelines

1. **Consistency is key**: Use annotation guidelines document
2. **Context matters**: Consider theological context
3. **Ambiguity**: When in doubt, tag with broader category
4. **Pronouns**:
   - "He" → DIVINE_PRONOUN (if referring to God)
   - "he" → HUMAN_PRONOUN (if referring to person)
5. **Titles vs. Names**:
   - "King David" → TITLE + PERSON (two separate spans)
   - Or use PERSON_TITLE (if in label_rules.yml)

---

### Keyboard Shortcuts

Learn and use keyboard shortcuts for speed:

| Key | Label | Example |
|-----|-------|---------|
| `d` | DEITY | God, LORD, Jesus |
| `p` | PERSON | Moses, David, Mary |
| `l` | LOCATION | Egypt, Jerusalem |
| `t` | TITLE | king, prophet, priest |
| `5` | TIME | seventh day, evening |
| `9` | PROPHET | Isaiah, Jeremiah |
| `[` | BIBLE_NATIONS | Israelites, Philistines |
| `]` | BIBLE_ANIMALS | lion, lamb, serpent |
| `c` | CONCEPT | love, justice, faith |

---

### Annotation Speed

Target speeds (with experience):
- **Manual annotation**: 50-100 verses/hour
- **Active learning**: 100-200 verses/hour
- **Pattern review**: 200-300 verses/hour

Total verses: ~31,000 verses
Estimated time (manual): 310-620 hours
**Recommendation**: Use active learning + patterns for efficiency

---

### Quality Targets

| Metric | Target | Priority |
|--------|--------|----------|
| Inter-Annotator Agreement (IAA) | ≥0.85 | High |
| Coverage (verses annotated) | 100% | High |
| Precision | ≥0.95 | High |
| Recall | ≥0.90 | Medium |
| Annotation consistency | ≥0.90 | High |

---

## Troubleshooting

### Problem: Prodigy won't start

**Error**: `ModuleNotFoundError: No module named 'prodigy'`

**Solution**:
```bash
pip install prodigy -f https://XXXX-XXXX-XXXX-XXXX@download.prodi.gy
```

---

### Problem: Patterns not loading

**Error**: Patterns file not found

**Solution**:
```bash
# Verify file exists
ls -lh prodigy_patterns.jsonl

# Use absolute path
prodigy ner.manual bible_gold blank:en ./silver_out/train.jsonl \
    --patterns /absolute/path/to/prodigy_patterns.jsonl
```

---

### Problem: Wrong labels displayed

**Solution**: Check `--label` parameter matches `label_rules.yml`:

```bash
# List all enabled labels
python -c "
import yaml
with open('label_rules.yml') as f:
    cfg = yaml.safe_load(f)
    print(','.join(cfg['labels']['enabled']))
"
```

---

### Problem: Slow annotation speed

**Solutions**:
1. Use `--patterns` to pre-suggest entities
2. Switch to `ner.teach` for active learning
3. Focus on high-priority labels only
4. Use keyboard shortcuts instead of mouse
5. Increase Prodigy batch size: `--batch-size 20`

---

### Problem: Database corruption

**Error**: `prodigy.util.DatabaseError`

**Solution**:
```bash
# Backup first
prodigy db-out bible_gold > backup.jsonl

# Drop and recreate
prodigy drop bible_gold
prodigy dataset bible_gold "Recreated dataset"

# Re-import
prodigy db-in bible_gold backup.jsonl
```

---

## Advanced Topics

### Custom Prodigy Recipe

Create custom recipe for biblical NER:

```python
# scripts/prodigy_recipes.py
import prodigy
from prodigy.components.loaders import JSONL
from prodigy.components.preprocess import add_tokens

@prodigy.recipe(
    "bible.ner.manual",
    dataset=("Dataset to save annotations", "positional", None, str),
    source=("Source JSONL file", "positional", None, str),
    labels=("Comma-separated labels", "option", "l", str),
)
def bible_ner_manual(dataset, source, labels=None):
    """
    Custom Prodigy recipe for biblical NER annotation.

    Features:
    - Display Strong's numbers as metadata
    - Show cross-references
    - Highlight divine names
    """
    stream = JSONL(source)
    stream = add_tokens(nlp, stream)

    # Custom preprocessing
    def add_metadata(eg):
        # Add Strong's, cross-refs, etc.
        return eg

    stream = (add_metadata(eg) for eg in stream)

    return {
        "dataset": dataset,
        "stream": stream,
        "view_id": "ner_manual",
        "config": {
            "labels": labels.split(",") if labels else [],
            "exclude_by": "task"
        }
    }
```

**Usage**:
```bash
python -m prodigy bible.ner.manual bible_gold ./silver_out/train.jsonl \
    -F scripts/prodigy_recipes.py \
    --label DEITY,PERSON,LOCATION
```

---

### Batch Annotation with Multiple Annotators

```bash
# Split data into batches
python scripts/split_batches.py \
    --input silver_out/train.jsonl \
    --output batches/ \
    --batch-size 1000

# Distribute to annotators
# Annotator 1: batches/batch_001.jsonl
# Annotator 2: batches/batch_002.jsonl
# etc.

# Merge after annotation
cat batches/batch_*_annotated.jsonl > merged_annotations.jsonl
```

---

## Next Steps

1. **Generate silver dataset** (if not done): `python code/silver_export.py`
2. **Install Prodigy** (requires license)
3. **Start annotation**: Use Workflow 1 or 2 above
4. **Track progress**: Monitor stats regularly
5. **Quality check**: Dual annotate 10% for IAA
6. **Export gold data**: `prodigy db-out bible_gold`
7. **Train final model**: Combine silver + gold

---

## Resources

- **Prodigy Docs**: https://prodi.gy/docs
- **spaCy NER Guide**: https://spacy.io/usage/linguistic-features#named-entities
- **Biblical NER Taxonomy**: See `DOCUMENTATION/Biblical_NLP_Taxonomy_Guide.md`
- **Label Rules**: See `label_rules.yml`

---

**Document Version**: 1.0
**Last Updated**: 2025-11-16
**Status**: Ready for Annotation Phase
