# Bible AI Database & NER Pipeline

A comprehensive Python-based system for biblical text analysis, named entity recognition (NER), and concordance generation. This project combines advanced web scraping, linguistic data processing, and machine learning to create structured biblical datasets with word-level annotations.

## Overview

This project provides:
- **Biblical Text Database**: Complete Bible text with cross-references (GoodBook.db)
- **Strong's Concordance Integration**: Automated scraping and lexicon enrichment
- **STEP Bible Parser**: Word-level alignment with Hebrew/Greek original languages
- **Sermon Corpus**: Automated sermon transcript collection from SermonIndex.net
- **NER Training Pipeline**: Silver dataset generation and spaCy model training
- **Linguistic Annotations**: POS tags, morphology, etymology, and semantic information

## Features

### Data Acquisition
- **Bible Text Scraping**: Optimized scraper with 15-20x performance improvements
- **Strong's Lexicon**: Batch scraper for Hebrew (H1-H8674) and Greek (G1-G5624) entries
- **STEP Bible Integration**: Morphologically-tagged text with original language alignment
- **Sermon Transcripts**: SermonIndex.net API integration with progress tracking

### NLP Pipeline
- **Token Alignment**: Greedy text-to-token alignment with 98.5% accuracy
- **Entity Labeling**: Rule-based NER using Strong's numbers, lemmas, and gazetteers
- **Dataset Generation**: Silver dataset export in spaCy/Prodigy JSONL format
- **Model Training**: Baseline spaCy NER model training with evaluation metrics

### Technical Highlights
- **Database Optimization**: Strategic indexing for 15-25% query speedup
- **Batch Processing**: executemany() for 99% reduction in DB round trips
- **Resume Capability**: Progress tracking for all long-running tasks
- **Configurable Pipeline**: YAML-based configuration with profile support

## Quick Start

### Prerequisites

```bash
# Python 3.8+
pip install -r requirements.txt

# Optional: For STEP Bible parsing
playwright install
```

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/Bible_AI_Database.git
cd Bible_AI_Database
pip install -r requirements.txt
```

### Basic Usage

```bash
# Run the interactive menu
python code/menu_master.py

# Or run individual components:

# 1. Scrape Bible text
python code/bible_scraper.py

# 2. Download Strong's concordance
python code/concordance_tools/strongs_batch_scraper.py

# 3. Scrape sermon transcripts
python code/sermon_scraper.py --speaker chuck_smith

# 4. Generate silver NER dataset
python code/silver_export.py --output silver_out

# 5. Train NER model
python code/train_baseline_spacy.py --data silver_out --output models/ner_v1
```

## Project Structure

```
bible/
├── code/                          # Main source code
│   ├── bible_scraper.py           # Optimized Bible text scraper
│   ├── sermon_scraper.py          # SermonIndex.net scraper
│   ├── silver_export.py           # NER dataset export
│   ├── silver_alignment.py        # Token-to-text alignment
│   ├── silver_label_rules.py      # Entity labeling rules
│   ├── train_baseline_spacy.py    # NER model training
│   ├── constants.py               # Project constants
│   ├── menu_master.py             # Interactive CLI menu
│   ├── STEP/                      # STEP Bible processing
│   │   ├── step_download_html.py  # Batch HTML download
│   │   ├── step_harvester.py      # Word-level data extraction
│   │   ├── step_parsers.py        # HTML parsing logic
│   │   ├── step_enrichment.py     # Lexicon enrichment
│   │   └── step_adapter.py        # Main orchestrator
│   └── utils/                     # Support utilities
│       ├── config_loader.py       # Configuration management
│       ├── logging_config.py      # Logging setup
│       └── path_config.py         # Path resolution
├── concordance_tools/             # Strong's concordance scrapers
│   ├── strongs_scraper.py         # Single entry scraper
│   └── strongs_batch_scraper.py   # Batch scraper
├── data/                          # Databases
│   ├── GoodBook.db                # Main Bible database
│   └── concordance.db             # (optional) Concordance DB
├── gazetteers/                    # Entity lists for NER
├── cache/                         # Cached HTML/JSON data
├── output/                        # Generated datasets
├── tests/                         # Unit tests
├── DOCUMENTATION/                 # Detailed docs
│   └── PROJECT_REPORT.md          # Comprehensive reference
├── label_rules.yml                # NER labeling rules
├── config.yaml                    # Main configuration
└── README.md                      # This file
```

## Pipeline Stages

### 1. Bible Text Scraping
**Script**: `code/bible_scraper.py`

Scrapes complete Bible text with cross-references from BibleGateway or similar sources.

**Optimizations**:
- Pre-loaded verse ID cache (eliminates 31,000+ queries)
- Batch inserts with `executemany()` (reduces 65,000+ queries to 1)
- Strategic database indexes for 15-25% additional speedup

**Output**: `data/GoodBook.db` (SQLite database)

### 2. Strong's Concordance Scraping
**Scripts**: `concordance_tools/strongs_scraper.py`, `strongs_batch_scraper.py`

Scrapes Hebrew (H1-H8674) and Greek (G1-G5624) lexicon entries from BlueLetterBible.

**Features**:
- Rate limiting (2-second delays)
- Resume capability
- Comprehensive metadata extraction

**Output**: `cache/STRONGS/{strongs_id}.json`

### 3. STEP Bible Data Acquisition
**Scripts**: `code/STEP/step_download_html.py`, `step_harvester.py`

Downloads morphologically-tagged Bible text from STEP Bible localhost server.

**Data Includes**:
- Original language (Hebrew/Greek) alignment
- Strong's numbers per word
- Morphology codes
- Lemmatization

**Output**: `cache/html/STEP_{book}{chapter}.html`

### 4. STEP HTML Parsing
**Script**: `code/STEP/step_parsers.py`

Parses STEP HTML into structured Token objects with full linguistic annotations.

**Features**:
- Dual parser support (selectolax 3-5x faster than BeautifulSoup)
- Document-level and verse-relative offsets
- Footnote extraction
- Plain text extraction

**Output**: Structured JSON files with tokens and annotations

### 5. Sermon Scraping
**Script**: `code/sermon_scraper.py`

Downloads sermon transcripts from SermonIndex.net.

**Features**:
- Speaker-based filtering
- Metadata + transcript download
- Progress tracking with resume
- Rate limiting

**Output**: `output/sermons/{speaker}/metadata/`, `output/sermons/{speaker}/transcripts/`

### 6. Silver Dataset Export
**Script**: `code/silver_export.py`

Generates NER training datasets from concordance database.

**Features**:
- Rule-based entity labeling (Strong's, lemmas, gazetteers)
- Greedy token-to-text alignment (98.5% accuracy)
- Phrase matching support
- Stratified train/dev/test splits

**Output**: `silver_out/{train,dev,test}.jsonl`

### 7. NER Model Training
**Script**: `code/train_baseline_spacy.py`

Trains spaCy NER models on silver datasets.

**Features**:
- Configurable epochs, batch size, labels
- Dev set evaluation after each epoch
- Best model checkpointing
- Final test set evaluation

**Output**: `models/{model_name}/best/`, `models/{model_name}/final/`

## Entity Types

The NER pipeline supports multiple entity types:

- `DEITY`: God, Lord, Holy Spirit
- `PERSON`: Biblical figures (Moses, David, Jesus)
- `LOCATION`: Places (Jerusalem, Egypt, Galilee)
- `GROUP`: People groups (Israelites, Pharisees)
- `EVENT`: Named events (Exodus, Passover)
- `PERSON_TITLE`: Titled persons (King David, Prophet Isaiah)
- `TIME`: Temporal expressions
- `ARTIFACT`: Objects of significance

Entity types are configured in `label_rules.yml`.

## Configuration

### Main Config: `config.yaml`

```yaml
database:
  goodbook_path: data/GoodBook.db
  concordance_path: data/concordance.db

paths:
  data_dir: data
  cache_dir: cache
  output_dir: output
  gazetteers_dir: gazetteers

silver_export:
  text_prefer: clean  # or 'plain', 'auto'
  seed: 13
  ratios: [0.8, 0.1, 0.1]  # train, dev, test
  require_clean: false
  align_report: true

logging:
  level: INFO
  log_dir: output/logs
```

### Label Rules: `label_rules.yml`

```yaml
labels:
  enabled:
    - DEITY
    - PERSON
    - LOCATION
    - GROUP

rules:
  DEITY:
    strongs_ids: [H0430, H3068, G2316, G2962]
    lemmas: [אֱלֹהִים, יְהוָה, θεός, κύριος]
    surfaces: [God, LORD, Lord]
    case_sensitive: true
    gazetteer_files:
      - gazetteers/deity.txt

merging:
  contiguous_merge: true

conflicts:
  priority: [DEITY, PERSON_TITLE, PERSON, LOCATION, GROUP]

phrases:
  override_labels: [PERSON_TITLE]
```

## Database Schema

### GoodBook.db

**Tables**:
- `books`: Book metadata (id, book_name, testament, chapter_count)
- `chapters`: Chapter metadata (id, book_id, chapter_number)
- `verses`: Verse data (id, chapter_id, verse_num, text, text_plain, text_clean)
- `tokens`: Token data (id, verse_id, text, strong_norm, token_idx)
- `cross_references`: Cross-references (source_verse_id, related_verse_id)

**Indexes**:
- `ix_verses_book_chapter_verse`
- `ix_chapters_book_chapter`
- `ix_xref_source`, `ix_xref_related`
- `ix_tokens_verse`, `ix_tokens_strongs`

## Performance

- **Bible Scraping**: 3-5 minutes (was 45-60 minutes)
- **Strong's Scraping**: ~2 hours for all 14,298 entries (with rate limiting)
- **STEP Download**: ~10-15 minutes for all 1,189 chapters
- **STEP Parsing**: ~30 seconds for entire Bible (with selectolax)
- **Silver Export**: ~2-3 minutes for 31,102 verses
- **NER Training**: ~5-10 minutes for 20 epochs (CPU)

## Testing

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_silver_alignment.py

# Run with coverage
pytest --cov=code --cov-report=html
```

## Documentation

Comprehensive documentation available in:
- `DOCUMENTATION/PROJECT_REPORT.md`: Complete technical reference
- `DOCUMENTATION/Biblical_NLP_Taxonomy_Guide.md`: Entity taxonomy
- `DOCUMENTATION/SERMONINDEX_API_SPEC.md`: API documentation

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **STEP Bible**: For morphologically-tagged Bible text
- **Blue Letter Bible**: For Strong's concordance data
- **SermonIndex.net**: For sermon transcripts
- **spaCy**: For NLP infrastructure
- **Prodigy**: For annotation tooling

## Contact

For questions or support, please open an issue on GitHub.

## Citation

If you use this project in academic research, please cite:

```bibtex
@software{bible_ai_database,
  author = {Your Name},
  title = {Bible AI Database \& NER Pipeline},
  year = {2025},
  url = {https://github.com/YOUR_USERNAME/Bible_AI_Database}
}
```
