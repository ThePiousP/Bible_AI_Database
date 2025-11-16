# PROJECT REPORT: Bible NER Pipeline

**Project:** Bible Named Entity Recognition & Concordance System
**Last Updated:** 2025-11-04
**Purpose:** Complete reference for AI assistants and developers

---

## QUICK REFERENCE FOR AI

### Critical Paths
```
code/
├── bible_scraper.py          → Bible text scraping (optimized 15x)
├── constants.py              → All project constants
├── train_baseline_spacy.py   → NER model training
├── silver_*.py               → Silver dataset generation (4 files)
├── STEP/                     → STEP Bible parsing (8 modules)
│   ├── step_download_html.py
│   ├── step_harvester.py
│   ├── step_enrichment.py
│   ├── step_parsers.py
│   ├── step_adapter.py
│   └── ...
└── utils/                    → Support utilities
    ├── config_loader.py
    ├── logging_config.py
    └── path_config.py

concordance_tools/
├── strongs_scraper.py        → Single Strong's entry scraper
└── strongs_batch_scraper.py  → Batch Strong's scraper

code/
├── sermon_scraper.py         → SermonIndex.net scraper
└── test_sermon_scraper.py    → Sermon scraper tests

data/
├── GoodBook.db               → Main Bible database
└── concordance.db (if exists)→ Concordance database

gazetteers/                   → Entity lists for NER
label_rules.yml               → NER labeling configuration
```

### Pipeline Stages Quick Map

| Stage | Key Files | Purpose |
|-------|-----------|---------|
| **1. Bible Text Scraping** | `bible_scraper.py` | Scrape verses, cross-refs → GoodBook.db |
| **2. Strong's Scraping** | `strongs_scraper.py`, `strongs_batch_scraper.py` | Scrape lexicon data → JSON files |
| **3. STEP Data Acquisition** | `STEP/step_download_html.py`, `step_harvester.py` | Get aligned Bible text with Strong's |
| **4. STEP Parsing** | `STEP/step_parsers.py`, `step_enrichment.py` | Parse HTML → structured tokens |
| **5. Sermon Scraping** | `sermon_scraper.py` | Scrape sermon transcripts from SermonIndex.net |
| **6. Silver Dataset Export** | `silver_export.py`, `silver_alignment.py` | Generate NER training data |
| **7. NER Training** | `train_baseline_spacy.py` | Train spaCy model on silver data |

### Most Important Functions - At A Glance

**Scraping:**
- `bible_scraper.py`: `build_verse_id_cache()`, `insert_cross_references_from_file_OPTIMIZED()`, `create_performance_indexes()`
- `strongs_scraper.py`: `scrape_strongs_entry(strongs_number)`
- `sermon_scraper.py`: `SermonScraper.scrape_speaker()`, `SermonIndexClient.get_speaker_sermons()`
- `STEP/step_download_html.py`: `download_all_html(version, options, output_dir)`
- `STEP/step_harvester.py`: `harvest_chapter(book, chap)`, `harvest_book(book)`

**NER Pipeline:**
- `silver_export.py`: `export_silver_dataset(db_path, rules_file, output_dir)`, `fetch_verses()`, `attach_tokens()`
- `silver_alignment.py`: `greedy_align_tokens_to_text()`, `build_spans_with_phrases()`
- `silver_label_rules.py`: `LabelRules.label_token()`, `phrase_labels_for_tokens()`
- `train_baseline_spacy.py`: `main()` (loads JSONL, trains model, evaluates)

**STEP Processing:**
- `step_parsers.py`: `parse_step_html()`, `parse_with_selectolax()`, `parse_with_bs4()`
- `step_enrichment.py`: `load_strongs_lexicon()`, `enrich_tokens_with_strongs()`
- `step_adapter.py`: `export_chapter()`, `batch_export_book()`

---

## DETAILED PIPELINE DOCUMENTATION

---

## 1. SCRAPING PIPELINE

### 1.1 Bible Text Scraping

#### `code/bible_scraper.py`
**Purpose:** Optimized Bible verse and cross-reference scraping (15-20x speedup)

**Key Functions:**

##### `build_verse_id_cache(conn: sqlite3.Connection) -> Dict[Tuple[str, int, int], int]`
- **Purpose:** Pre-load all verse IDs into memory for instant lookups
- **Parameters:**
  - `conn`: SQLite database connection
- **Returns:** Dictionary mapping `(book_name, chapter_num, verse_num)` → `verse_id`
- **Performance:** Single query replaces 31,000+ individual queries
- **Example:**
  ```python
  cache = build_verse_id_cache(conn)
  verse_id = cache[("Genesis", 1, 1)]  # Instant lookup
  ```

##### `insert_cross_references_from_file_OPTIMIZED(file_path, db_path, resolve_abbreviation_func, expand_verse_range_func)`
- **Purpose:** Batch insert cross-references with 15-20x speedup
- **Parameters:**
  - `file_path`: Path to cross-reference TSV file
  - `db_path`: Path to SQLite database
  - `resolve_abbreviation_func`: Function to resolve book abbreviations
  - `expand_verse_range_func`: Function to expand verse ranges
- **Returns:** None (modifies database)
- **Optimizations:**
  1. Pre-load verse IDs (1 query vs 31,000+)
  2. Batch INSERT with executemany() (1 query vs 65,000+)
  3. Reduce DB round trips by 99%
- **Performance:** 3-5 minutes (was 45-60 minutes)

##### `create_performance_indexes(db_path: str)`
- **Purpose:** Create database indexes for 15-25% additional speedup
- **Parameters:**
  - `db_path`: Path to SQLite database
- **Returns:** None (modifies database)
- **Indexes Created:**
  - `ix_verses_book_chapter_verse` (verse lookups)
  - `ix_chapters_book_chapter` (chapter lookups)
  - `ix_xref_source`, `ix_xref_related` (cross-reference queries)
  - `ix_tokens_verse`, `ix_tokens_strongs` (token queries)

##### `optimize_bible_scraper(scraper_instance, cross_ref_file, db_path)`
- **Purpose:** Apply all optimizations to BibleScraper instance
- **Parameters:**
  - `scraper_instance`: Instance of BibleScraper class
  - `cross_ref_file`: Path to cross-reference file
  - `db_path`: Path to database
- **Returns:** None (applies optimizations)
- **Expected Speedup:** 15-20x faster

---

### 1.2 Strong's Concordance Scraping

#### `concordance_tools/strongs_scraper.py`
**Purpose:** Scrape individual Strong's lexicon entries from BlueLetterBible

**Key Functions:**

##### `scrape_strongs_entry(strongs_number: str) -> Dict`
- **Purpose:** Scrape a single Strong's entry
- **Parameters:**
  - `strongs_number`: Strong's number (e.g., "H430", "G2316")
- **Returns:** Dictionary with lexicon data:
  - `lemma`: Original language word
  - `transliteration`: Romanized pronunciation
  - `pronunciation`: Phonetic pronunciation
  - `pos`: Part of speech
  - `etymology`: Word origin
  - `kjv_translation_count`: KJV usage statistics
  - `outline`: Outline of biblical usage
  - `definition`: Strong's definition
- **Output:** Saves JSON file to `output/concordance/{strongs_id}.json`
- **Logging:** Saves progress to `output/logs/strongs_scraper_log.json`

##### `clean_text(text: str) -> str`
- **Purpose:** Clean scraped text (remove artifacts, fix spacing)
- **Parameters:** `text`: Raw text string
- **Returns:** Cleaned text string

##### `extract_kjv_translation(text: str) -> str`
- **Purpose:** Extract KJV translation count information
- **Parameters:** `text`: Raw KJV translation text
- **Returns:** Cleaned translation count string

##### `split_outline_text(text: str) -> List[str]`
- **Purpose:** Split outline text into segments
- **Parameters:** `text`: Raw outline text
- **Returns:** List of outline segments

**Helper Functions:**
- `save_json(data)`: Save entry to JSON file
- `save_log(log_data)`: Append to scraping log

---

#### `concordance_tools/strongs_batch_scraper.py`
**Purpose:** Batch scrape all Strong's entries (Hebrew & Greek)

**Key Functions:**

##### `scrape_batch()`
- **Purpose:** Scrape all Strong's entries with progress tracking
- **Parameters:** None (uses config constants)
- **Returns:** None (saves to files)
- **Features:**
  - Rate limiting (2 seconds between requests)
  - Progress tracking (completed/failed IDs saved)
  - Resume capability (skips already completed)
  - Configurable mode (H, G, or ALL)
- **Output:**
  - JSON files: `output/concordance/{strongs_id}.json`
  - Progress: `output/logs/completed_ids.json`, `failed_ids.json`

##### `get_next_strongs_ids(mode: str) -> List[str]`
- **Purpose:** Generate list of Strong's IDs to scrape
- **Parameters:**
  - `mode`: "H" (Hebrew), "G" (Greek), or "ALL"
- **Returns:** List of Strong's IDs (e.g., ["H1", "H2", ..., "G1", "G2", ...])
- **Ranges:**
  - Hebrew: H1-H8674
  - Greek: G1-G5624

**Helper Functions:**
- `load_json_list(path)`: Load progress tracking JSON
- `save_json_list(data, path)`: Save progress tracking JSON

**Configuration:**
- `RATE_LIMIT`: 2.0 seconds (adjustable)
- `MAX_ENTRIES_PER_RUN`: None (no limit, can be set)
- `MODE`: "ALL" (can be "H" or "G")

---

### 1.3 Sermon Scraping (SermonIndex)

#### `code/sermon_scraper.py`
**Purpose:** Download sermon metadata and transcripts from SermonIndex.net API

**Key Classes:**

##### `SermonScraper`
**Purpose:** Main orchestrator for sermon scraping with progress tracking

**Initialization:**
```python
scraper = SermonScraper(
    speaker_code="chuck_smith",
    output_dir=Path("output/sermons"),
    log_dir=Path("output/logs"),
    logger=logger,
    max_sermons=None,  # None = all sermons
    resume=True
)
```

**Key Method:**

##### `scrape_speaker() -> Dict`
- **Purpose:** Scrape all sermons for a specific speaker
- **Parameters:** None (uses instance settings)
- **Returns:** Statistics dictionary with:
  - `speaker`: Speaker code
  - `total_found`: Total sermons discovered
  - `processed`: Newly processed sermons
  - `skipped`: Already completed (resume mode)
  - `failed`: Failed sermons
  - `elapsed_seconds`: Total time
  - `elapsed_minutes`: Total time in minutes
- **Features:**
  - Progress tracking (resume capability)
  - Rate limiting (2-second delays)
  - Metadata + transcript download
  - Comprehensive logging
- **Output Structure:**
  ```
  output/sermons/{speaker}/
  ├── metadata/
  │   ├── {sermon_id}.json
  │   └── ...
  └── transcripts/
      ├── {sermon_id}.txt
      └── ...
  ```

##### `SermonIndexClient`
**Purpose:** API client with rate limiting for SermonIndex.net

**Key Methods:**

##### `get_speaker_sermons(speaker_code: str, use_github: bool = True) -> List[Dict]`
- **Purpose:** Fetch all sermons for a speaker from API
- **Parameters:**
  - `speaker_code`: Speaker code (e.g., "chuck_smith")
  - `use_github`: Use GitHub endpoint (more reliable) vs direct API
- **Returns:** List of sermon dictionaries
- **Rate Limiting:** 2-second delay between requests

##### `download_text_content(url: str) -> Optional[str]`
- **Purpose:** Download transcript text from URL
- **Parameters:**
  - `url`: Transcript URL (TXT, VTT, SRT)
- **Returns:** Text content or None if failed
- **Features:** Handles multiple content types

##### `SermonMetadata` (dataclass)
**Purpose:** Structured sermon metadata

**Fields:**
- `sermon_id`: Unique identifier
- `title`: Sermon title
- `speaker`: Speaker name
- `scripture_refs`: Bible references
- `topics`: Topic tags
- `series`: Series name
- `date`: Sermon date
- `duration`: Length (mm:ss)
- `play_count`: Play statistics
- `download_url_mp3`: Audio file URL
- `download_url_txt`: Transcript URL
- `download_url_pdf`: PDF URL
- `download_url_srt`: SRT subtitle URL
- `download_url_vtt`: WebVTT subtitle URL
- `source_url`: Original page URL
- `scraped_at`: ISO timestamp

##### `ProgressTracker`
**Purpose:** Track scraping progress with resume capability

**Key Methods:**
- `mark_completed(sermon_id)`: Mark sermon as successfully scraped
- `mark_failed(sermon_id)`: Mark sermon as failed
- `is_completed(sermon_id)`: Check if already scraped
- `get_stats()`: Get progress statistics

**Files Created:**
- `sermon_progress.json`: Overall progress summary
- `sermon_completed.json`: List of completed sermon IDs
- `sermon_failed.json`: List of failed sermon IDs

**Usage:**
```bash
# Scrape all sermons for Chuck Smith
python sermon_scraper.py --speaker chuck_smith

# Scrape first 100 sermons
python sermon_scraper.py --speaker chuck_smith --max-sermons 100

# Start fresh (no resume)
python sermon_scraper.py --speaker chuck_smith --no-resume

# Debug mode
python sermon_scraper.py --speaker chuck_smith --log-level DEBUG
```

**Menu Integration:**
- **Menu Option:** 4. Run Sermon Scraper (SermonIndex)
- **Config Keys:**
  - `sermon_speaker`: Default speaker code
  - `sermon_output_dir`: Output directory
  - `sermon_log_dir`: Log directory
  - `sermon_max_sermons`: Max sermons per run (None = all)
  - `sermon_resume`: Resume from previous run

---

### 1.4 STEP Bible Data Acquisition

#### `code/STEP/step_download_html.py`
**Purpose:** Download all Bible chapter HTML files from STEP Bible localhost server

**Key Functions:**

##### `download_all_html(version, options, output_dir, wait_ms)`
- **Purpose:** Download all 1,189 Bible chapters as HTML files
- **Parameters:**
  - `version`: Bible version code (e.g., "KJV", "ESV")
  - `options`: STEP options string (e.g., "NHVUG" for Strong's, morphology, etc.)
  - `output_dir`: Directory to save HTML files (default: `cache/html`)
  - `wait_ms`: Milliseconds to wait after page load (default: 500)
- **Returns:** None (saves HTML files)
- **Output:** Files named `STEP_{osis}{chapter}.html` (e.g., `STEP_Gen1.html`)
- **Performance:** Uses single browser instance for all chapters
- **Progress:** Real-time progress display with percentage

**Features:**
- Single browser launch (reused for all chapters)
- Proper handling of single-chapter books (Obadiah, Philemon, etc.)
- Timeout handling (60 seconds per chapter)
- Error reporting with failed chapter list

**Usage:**
```bash
python step_download_html.py --version KJV --options NHVUG --output cache/html
```

---

#### `code/STEP/step_harvester.py`
**Purpose:** Extract per-word alignment data from STEP Bible HTML (alternative to download approach)

**Key Functions:**

##### `harvest_chapter(book: str, chap: int) -> List[WordRec]`
- **Purpose:** Harvest word-level data from a single chapter
- **Parameters:**
  - `book`: Book name (e.g., "Genesis")
  - `chap`: Chapter number (1-based)
- **Returns:** List of `WordRec` objects with:
  - `book_name`, `chapter_number`, `verse_number`
  - `token_index` (1-based within verse)
  - `surface` (display text)
  - `strongs` (Strong's number)
  - `lemma` (original language)
  - `morph` (morphology code)
  - `lang` (Hebrew/Greek)
- **Output:** Optional JSON file and/or SQLite insertion

##### `harvest_book(book: str, chapter_count: Optional[int]) -> Dict[int, List[WordRec]]`
- **Purpose:** Harvest an entire book
- **Parameters:**
  - `book`: Book name
  - `chapter_count`: Total chapters (optional, auto-detects if None)
- **Returns:** Dictionary mapping chapter numbers to word records
- **Features:**
  - Auto-detection of chapter count (tries up to 200, stops after 2 failures)
  - Progress tracking

**Data Model:**

##### `WordRec` (dataclass)
- **Fields:**
  - `book_name`: str
  - `chapter_number`: int
  - `verse_number`: int
  - `token_index`: int (1-based)
  - `surface`: str (word text)
  - `strongs`: str (Strong's ID)
  - `lemma`: str (original language)
  - `morph`: str (morphology)
  - `lang`: str (Hebrew/Greek)

**Helper Functions:**
- `create_alignment_table(db_path)`: Create `word_index` table
- `insert_records(db_path, rows)`: Insert records into SQLite
- `write_chapter_json(out_root, book, chap, rows)`: Write JSON file

**Usage:**
```bash
# Single chapter
python step_harvester.py --mode chapter --book Genesis --chapter 22

# Whole book
python step_harvester.py --mode book --book Genesis

# With SQLite output
python step_harvester.py --mode book --book Genesis --sqlite GoodBook.db
```

---

### 1.5 STEP HTML Parsing

#### `code/STEP/step_parsers.py`
**Purpose:** Parse STEP HTML into structured token data with linguistic annotations

**Data Models:**

##### `Token` (dataclass)
**Purpose:** Represents a single word/token with full linguistic annotations

**Key Fields:**
- `text`: Display text of the token
- `strong_norm`: Normalized Strong's number (e.g., "H0430")
- `strong_raw`: Raw Strong's attribute from HTML
- `morph_norm`: Normalized morphology code
- `morph_raw`: Raw morphology attribute
- `italics`: Whether token is italicized (supplied words)
- `html_start`, `html_end`: Document-level character offsets
- `vhtml_start`, `vhtml_end`: Verse-relative HTML offsets
- `morph_gloss`: Human-readable morphology description
- `morph_features`: Structured morphology features dict
- `lemma`: Strong's lexicon lemma (original language)
- `transliteration`: Romanized pronunciation
- `pronunciation`: Phonetic pronunciation
- `pos`: Part of speech
- `definition`: Strong's definition
- `kjv_translation_count`: Raw KJV translation count string
- `kjv_counts`: Structured KJV counts (parsed)
- `etymology`: Etymology information
- `outline`: Outline of biblical usage
- `text_start`, `text_end`: Plain text character offsets
- `token_id`: Unique token identifier (e.g., "Gen.1.1#t0000")

##### `Footnote` (dataclass)
**Fields:**
- `marker`: Footnote marker (e.g., 'a', 'b', '1')
- `notetype`: Type of note ("xref", "textual", "translation")
- `ref_attr`: Reference attribute from `<a>` tag
- `xref_attr`: Cross-reference attribute
- `body_text`: Plain text of footnote
- `body_html`: HTML of footnote

##### `Verse` (dataclass)
**Fields:**
- `ref`: OSIS reference (e.g., "Gen.1.1")
- `verse_num`: Verse number within chapter
- `text_plain`: Plain text of verse (no HTML)
- `verse_html`: Raw HTML of verse
- `tokens`: List of Token objects
- `footnotes`: List of Footnote objects

**Key Functions:**

##### `parse_step_html(html, include_italics, parser, verbose) -> List[Verse]`
- **Purpose:** Unified parser interface (auto-selects selectolax or BS4)
- **Parameters:**
  - `html`: Full chapter HTML
  - `include_italics`: Include italics tokens (default: True)
  - `parser`: "auto", "selectolax", or "bs4"
  - `verbose`: Print warnings
- **Returns:** List of Verse objects
- **Selection Logic:**
  - Tries selectolax first (faster)
  - Falls back to BS4 if selectolax not available

##### `parse_with_selectolax(html, include_italics) -> List[Verse]`
- **Purpose:** Fast HTML parsing with selectolax
- **Parameters:**
  - `html`: Full chapter HTML
  - `include_italics`: Include italics tokens
- **Returns:** List of Verse objects
- **Performance:** ~3-5x faster than BeautifulSoup
- **Features:**
  - Document-level and verse-relative offsets
  - Automatic token ID assignment
  - Plain text extraction
  - Footnote parsing

##### `parse_with_bs4(html, include_italics) -> List[Verse]`
- **Purpose:** Fallback HTML parsing with BeautifulSoup4
- **Parameters:** Same as `parse_with_selectolax`
- **Returns:** List of Verse objects
- **Features:** Same semantics as selectolax parser

**Helper Functions:**
- `plain_text_from_verse(v)`: Extract plain text from verse node
- `_node_has_ancestor_with_class(node, class_name)`: Check ancestor class
- `align_text_offsets(plain, tokens)`: Compute text offsets for tokens

---

### 1.6 STEP Enrichment

#### `code/STEP/step_enrichment.py`
**Purpose:** Load Strong's lexicon and enrich tokens with linguistic data

**Key Functions:**

##### `load_strongs_lexicon(dir_hints, verbose) -> Dict[str, Dict[str, Any]]`
- **Purpose:** Recursively load all Strong's entries from JSON files
- **Parameters:**
  - `dir_hints`: Optional list of custom directories to search
  - `verbose`: Print diagnostic info during loading
- **Returns:** Dictionary mapping Strong's numbers (e.g., "H0430") to metadata
- **Search Paths (in order):**
  1. Custom directories (if provided)
  2. `cache/STRONGS` (Phase 1 standard)
  3. `strongs_json`, `strongs`, `STRONGS`
  4. `lexicon`, `data/strongs`
  5. Current directory
- **File Formats Supported:**
  - Single-object JSON (with `strongs_number` field)
  - Array of objects JSON (each with `strongs_number`)
- **Performance:** Loads 8,000+ entries in ~1-2 seconds

##### `enrich_tokens_with_strongs(tokens, strongs_index)`
- **Purpose:** In-place enrichment of Token objects with Strong's data
- **Parameters:**
  - `tokens`: List of Token objects (modified in-place)
  - `strongs_index`: Dictionary from `load_strongs_lexicon()`
- **Returns:** None (modifies tokens in-place)
- **Enriched Fields:**
  - `lemma`: Original language word
  - `transliteration`: Romanized pronunciation
  - `pronunciation`: Phonetic pronunciation
  - `pos`: Part of speech
  - `definition`: Strong's definition
  - `kjv_translation_count`: KJV usage statistics
  - `kjv_counts`: Structured KJV counts (parsed)
  - `etymology`: Etymology information
  - `outline`: Outline of biblical usage
- **Logic:** Only enriches missing fields (preserves existing data)

##### `strongs_key(s: str) -> Optional[str]`
- **Purpose:** Normalize H/G key to canonical format (zero-padded to 4 digits)
- **Parameters:** `s`: Strong's number string
- **Returns:** Normalized key (e.g., "H0430", "G5624"), or None if invalid
- **Examples:**
  - `strongs_key("H430")` → `"H0430"`
  - `strongs_key("g1")` → `"G0001"`

##### `normalize_kjv_counts(raw: Optional[str]) -> Optional[List[Dict[str, Any]]]`
- **Purpose:** Parse KJV translation count strings into structured format
- **Parameters:** `raw`: Raw KJV count string
- **Returns:** List of `{"gloss": str, "count": int}` dicts, or None if empty
- **Example:**
  - Input: `"after (454x), follow (78x)"`
  - Output: `[{"gloss": "after", "count": 454}, {"gloss": "follow", "count": 78}]`

**Helper Functions:**
- `collect_strongs_dirs(custom_dirs)`: Build search list for Strong's JSON folders
- `get_cached_lexicon(dir_hints, verbose)`: Get cached lexicon (loads on first call)
- `reset_lexicon_cache()`: Reset the global Strong's cache

---

### 1.7 STEP Adapter (Main Orchestrator)

#### `code/STEP/step_adapter.py`
**Purpose:** Main orchestrator for STEP data processing with backward-compatible imports

**Key Functions:**

##### `export_chapter(source, out_path, include_italics, parser, verbose)`
- **Purpose:** Export a single chapter to structured JSON
- **Parameters:**
  - `source`: URL, file path, or OSIS reference
  - `out_path`: Output JSON path
  - `include_italics`: Include italics tokens (default: True)
  - `parser`: "auto", "selectolax", or "bs4"
  - `verbose`: Print warnings
- **Returns:** Dictionary with export statistics
- **Output JSON Structure:**
  ```json
  {
    "ref": "Gen.1",
    "book": "Genesis",
    "chapter": 1,
    "version": "KJV",
    "verses": [
      {
        "ref": "Gen.1.1",
        "verse_num": 1,
        "text_plain": "In the beginning...",
        "tokens": [...],
        "footnotes": [...]
      }
    ]
  }
  ```

##### `batch_export_book(book, start, end, source_mode, version, options, html_dir, output_dir, include_italics, parser, continue_on_error, log_dir, verbose)`
- **Purpose:** Export multiple chapters of a book
- **Parameters:**
  - `book`: Book name (e.g., "Genesis")
  - `start`: Start chapter (1-based)
  - `end`: End chapter (inclusive)
  - `source_mode`: "url" (fetch from localhost) or "file" (use cached HTML)
  - `version`: Bible version code
  - `options`: STEP options string
  - `html_dir`: Directory for cached HTML (if source_mode="file")
  - `output_dir`: Output directory for JSON files
  - `include_italics`: Include italics tokens
  - `parser`: Parser to use
  - `continue_on_error`: Continue if a chapter fails
  - `log_dir`: Log directory
  - `verbose`: Print warnings
- **Returns:** Dictionary with `{"ok": [...], "failed": [...], "log": "..."}`
- **Features:**
  - Progress tracking
  - Error handling with continue-on-error option
  - Logging to file

##### `batch_export_full_bible(...)`
- **Purpose:** Export all 66 books of the Bible
- **Parameters:** Similar to `batch_export_book()`
- **Returns:** Dictionary with statistics
- **Features:** Iterates through all books in canonical order

**Re-exported APIs (Backward Compatibility):**
- Constants: `BOOK_CHAPTERS`, `BOOK_INDEX`, `BOOK_OSIS`, etc.
- Normalization: `normalize_strongs()`, `normalize_morph()`, `decode_morph()`
- Enrichment: `load_strongs_lexicon()`, `enrich_tokens_with_strongs()`
- Alignment: `align_text_offsets()`, `fuzzy_find()`, `collapse()`
- Parsers: `Token`, `Verse`, `Footnote`, `parse_step_html()`
- CLI: `settings_menu()`, `run_menu()`

---

## 2. NER (NAMED ENTITY RECOGNITION) PIPELINE

### 2.1 Silver Dataset Generation

#### `code/silver_export.py`
**Purpose:** Main orchestrator for silver NER dataset export from concordance database

**Key Functions:**

##### `export_silver_dataset(db_path, rules_file, output_dir, text_prefer, seed, ratios, holdout_books, holdout_name, require_clean, align_report, label_on_miss) -> Dict[str, Any]`
- **Purpose:** Export complete silver NER dataset from concordance database
- **Parameters:**
  - `db_path`: Path to SQLite database (e.g., `concordance.db`)
  - `rules_file`: Path to `label_rules.yml`
  - `output_dir`: Output directory for JSONL files (default: `silver_out`)
  - `text_prefer`: "auto", "clean", or "plain" (which text column to use)
  - `seed`: Random seed for reproducible splits (default: 13)
  - `ratios`: `(train, dev, test)` split ratios (default: (0.8, 0.1, 0.1))
  - `holdout_books`: Books to exclude from training (domain holdout)
  - `holdout_name`: Name for holdout split (default: "domain_holdout")
  - `require_clean`: Require `text_clean` column (error if missing)
  - `align_report`: Print alignment statistics
  - `label_on_miss`: Default label for unmatched tokens (optional)
- **Returns:** Dictionary with statistics:
  ```python
  {
      "total_verses": 31102,
      "total_tokens": 790000,
      "total_examples": 28500,
      "train_count": 22800,
      "dev_count": 2850,
      "test_count": 2850,
      "text_column": "text_clean"
  }
  ```
- **Output Files:**
  - `{output_dir}/train.jsonl`
  - `{output_dir}/dev.jsonl`
  - `{output_dir}/test.jsonl`
- **JSONL Format:**
  ```json
  {
    "text": "In the beginning God created the heaven and the earth.",
    "spans": [
      {"start": 17, "end": 20, "label": "DEITY"}
    ],
    "meta": {
      "book": "Genesis",
      "chapter": 1,
      "verse": 1,
      "verse_id": 1
    }
  }
  ```

##### `fetch_verses(conn, schema, holdout_books) -> List[Verse]`
- **Purpose:** Fetch all verses from database
- **Parameters:**
  - `conn`: Database connection
  - `schema`: SchemaInfo object (which text column to use)
  - `holdout_books`: Books to exclude (optional)
- **Returns:** List of Verse objects
- **SQL Query:** Joins verses, chapters, books tables

##### `attach_tokens(conn, verses) -> None`
- **Purpose:** Attach tokens to verses (in-place modification)
- **Parameters:**
  - `conn`: Database connection
  - `verses`: List of Verse objects (modified in-place)
- **Returns:** None (modifies verses in-place)
- **SQL Query:** Fetches tokens with Strong's IDs, ordered by verse and token index

##### `detect_schema(conn, text_prefer) -> SchemaInfo`
- **Purpose:** Detect database schema and determine which text column to use
- **Parameters:**
  - `conn`: Database connection
  - `text_prefer`: "auto", "clean", or "plain"
- **Returns:** `SchemaInfo` object with:
  - `has_text_plain`: bool
  - `has_text_clean`: bool
  - `text_prefer`: str
  - `text_column`: str (resolved column name)
- **Logic:**
  - If `text_prefer="clean"` → use `text_clean` if exists, else fallback
  - If `text_prefer="plain"` → use `text_plain` if exists, else fallback
  - If `text_prefer="auto"` → prefer `text_clean`, else `text_plain`, else `text`

##### `stratified_split(items, by_key, ratios, seed) -> Tuple[List, List, List]`
- **Purpose:** Stratify items by key and split into train/dev/test
- **Parameters:**
  - `items`: List of dictionaries
  - `by_key`: Key to stratify by (e.g., "book")
  - `ratios`: `(train, dev, test)` ratios (must sum to 1.0)
  - `seed`: Random seed for reproducibility
- **Returns:** Tuple of `(train, dev, test)` lists
- **Logic:** Splits each stratum (book) proportionally, then combines

**Helper Functions:**
- `has_column(conn, table, col)`: Check if table has column
- `write_jsonl(path, rows, show_progress)`: Write list of dicts to JSONL file

---

#### `code/silver_alignment.py`
**Purpose:** Greedy text alignment and span building for silver NER

**Key Functions:**

##### `greedy_align_tokens_to_text(verse_text, token_surfaces) -> Tuple[List[Tuple[int, int]], int]`
- **Purpose:** Left-to-right greedy alignment of tokens to verse text
- **Parameters:**
  - `verse_text`: Plain text of verse
  - `token_surfaces`: List of token strings
- **Returns:** Tuple of:
  - List of `(start, end)` character offsets for each token
  - Number of alignment misses (tokens not found)
- **Algorithm:**
  1. Start with cursor at position 0
  2. For each token:
     - Try exact match from cursor
     - If fails, try with collapsed spaces (fallback)
     - Record `(start, end)` or `(-1, -1)` if not found
     - Advance cursor to end of match
- **Performance:**
  - Time: O(n * m) where n=tokens, m=avg verse length (~50 chars)
  - Space: O(n) for spans list
  - Typical: 98.5% alignment success rate
- **Example:**
  ```python
  text = "In the beginning God created"
  tokens = ["In", "the", "beginning", "God", "created"]
  spans, misses = greedy_align_tokens_to_text(text, tokens)
  # spans = [(0, 2), (3, 6), (7, 16), (17, 20), (21, 28)]
  # misses = 0
  ```

##### `build_spans_with_phrases(verse, rules) -> List[Span]`
- **Purpose:** Build labeled spans with phrase matching support
- **Parameters:**
  - `verse`: Verse object with tokens
  - `rules`: LabelRules object
- **Returns:** List of Span objects
- **Steps:**
  1. Align tokens to verse text (greedy)
  2. Get phrase labels (per-token)
  3. Get phrase override mask (highest priority)
  4. Combine labels with priority: override > phrase > per-token
  5. Merge consecutive tokens with same label (if enabled)
- **Priority:**
  1. Phrase override labels (highest)
  2. Phrase labels
  3. Per-token labels (lowest)
- **Example:** "King David" might match phrase "King David" → PERSON_TITLE instead of two separate tokens

##### `build_spans(verse, rules) -> List[Span]`
- **Purpose:** Build labeled spans for a verse (without phrase matching)
- **Parameters:**
  - `verse`: Verse object with tokens
  - `rules`: LabelRules object
- **Returns:** List of Span objects
- **Steps:**
  1. Greedy alignment (once per verse)
  2. Label each token using rules
  3. Create spans for labeled tokens
  4. Merge contiguous spans with same label (if enabled)

##### `calculate_alignment_stats(verses) -> dict`
- **Purpose:** Calculate alignment quality statistics
- **Parameters:** `verses`: List of Verse objects (with `align_spans` set)
- **Returns:** Dictionary with:
  - `total_tokens`: int
  - `aligned`: int
  - `unaligned`: int
  - `success_rate`: float
  - `avg_verse_length`: float
  - `avg_tokens_per_verse`: float

---

#### `code/silver_label_rules.py`
**Purpose:** Label matching rules for NER annotation

**Key Class:**

##### `LabelRules`
**Purpose:** Manages label matching rules for NER annotation

**Initialization:**
```python
rules = LabelRules(cfg, label_on_miss=None)
```
- **Parameters:**
  - `cfg`: Configuration dictionary from `label_rules.yml`
  - `label_on_miss`: Optional label for unmatched tokens

**Configuration Format:**
```yaml
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
```

**Key Methods:**

##### `label_token(tok: Token) -> Optional[str]`
- **Purpose:** Determine single label for token (or None)
- **Parameters:** `tok`: Token object
- **Returns:** Label string or None
- **Matches by:**
  1. Strong's ID
  2. Lemma
  3. Surface form
- **Conflict Resolution:** Uses priority list
- **Example:**
  ```python
  token = Token(surface="God", strongs_id="H0430")
  label = rules.label_token(token)  # Returns "DEITY"
  ```

##### `phrase_labels_for_tokens(tokens: List[Token]) -> List[Optional[str]]`
- **Purpose:** Assign phrase labels to tokens (per-token basis)
- **Parameters:** `tokens`: List of Token objects
- **Returns:** List of labels (one per token), None if no match
- **Features:**
  - Contiguous matching (tokens must match phrase exactly, no gaps)
  - Conflict resolution using global priority list
- **Example:**
  ```python
  tokens = [Token("King"), Token("David")]
  labels = rules.phrase_labels_for_tokens(tokens)
  # Returns ['PERSON_TITLE', 'PERSON_TITLE']
  ```

##### `phrase_override_mask(tokens: List[Token]) -> List[Optional[str]]`
- **Purpose:** Return per-token mask of override phrase labels
- **Parameters:** `tokens`: List of Token objects
- **Returns:** List of override labels (one per token), None if no override
- **Logic:** Override labels take precedence over per-token labels within matched phrase window

**Helper Methods:**
- `_build_lookup_structures()`: Build internal lookup structures from rules
- `_load_gazetteer(path)`: Load gazetteer from file (CSV, TSV, TXT, JSON)

**Supported Gazetteer Formats:**
- **CSV/TSV:** First column is surface string
- **TXT:** One entry per line (# for comments)
- **JSON:** `list[str]` or `list[dict]` with 'name' key

---

#### `code/silver_data_models.py`
**Purpose:** Data structures for silver NER dataset export

**Data Models:**

##### `Token` (dataclass)
**Purpose:** Represents a single token/word with linguistic annotations

**Fields:**
- `surface`: str (text of token)
- `strongs_id`: Optional[str] (e.g., "H0430", "G2316")
- `lemma`: Optional[str] (dictionary form in original language)
- `pos`: Optional[str] (part of speech tag)

##### `Verse` (dataclass)
**Purpose:** Represents a single Bible verse with tokens

**Fields:**
- `verse_id`: int (unique verse ID from database)
- `book`: str (e.g., "Genesis", "Matthew")
- `chapter`: int (1-indexed)
- `verse`: int (1-indexed)
- `text`: str (plain text of verse)
- `tokens`: List[Token] (tokens in database order)
- `align_spans`: List[Tuple[int, int]] (character offsets aligned to text)

**Methods:**
- `__str__()`: Returns `"{book} {chapter}:{verse}"`
- `get_ref()`: Returns `"{book}.{chapter}.{verse}"`

##### `Span` (dataclass)
**Purpose:** Represents a labeled text span (entity) in NER format

**Fields:**
- `start`: int (character offset, 0-indexed)
- `end`: int (character offset, exclusive)
- `label`: str (entity label, e.g., "PERSON", "DEITY")

**Methods:**
- `__len__()`: Returns length of span in characters
- `__str__()`: Returns `"[{start}:{end}]={label}"`
- `overlaps(other)`: Check if this span overlaps with another
- `contains(other)`: Check if this span fully contains another

##### `NERExample` (dataclass)
**Purpose:** Represents a complete NER training example

**Fields:**
- `text`: str (plain text string)
- `spans`: List[Span] (labeled spans)
- `meta`: dict (metadata: book, chapter, verse, etc.)

**Methods:**
- `to_dict()`: Convert to spaCy training format
- `to_prodigy_format()`: Convert to Prodigy annotation format

##### `SchemaInfo` (dataclass)
**Purpose:** Database schema information

**Fields:**
- `has_text_plain`: bool
- `has_text_clean`: bool
- `text_prefer`: str ("auto", "clean", "plain")
- `text_column`: str (resolved SQL column name)

---

### 2.2 NER Model Training

#### `code/train_baseline_spacy.py`
**Purpose:** Train a spaCy NER baseline model from silver JSONL dataset

**Key Functions:**

##### `main()`
- **Purpose:** Main training pipeline
- **Parameters:** Command-line arguments (parsed by argparse)
- **Steps:**
  1. Load train/dev/test JSONL files
  2. Initialize spaCy pipeline (blank or pretrained)
  3. Register NER labels
  4. Build training examples (docs with gold spans)
  5. Train for N epochs with dev evaluation
  6. Save best model (by dev F1 score)
  7. Final evaluation on test set
- **Output:**
  - Best model: `{output_dir}/best/`
  - Final model: `{output_dir}/final/`
  - Test metrics printed to console

##### `load_jsonl(path: str) -> List[Dict[str, Any]]`
- **Purpose:** Load JSONL file into list of dictionaries
- **Parameters:** `path`: Path to JSONL file
- **Returns:** List of dictionaries (one per line)

##### `make_docs(nlp, rows, labels, warn_dropout) -> Tuple[List[Doc], int]`
- **Purpose:** Convert JSONL rows to spaCy Doc objects with gold entities
- **Parameters:**
  - `nlp`: spaCy model
  - `rows`: List of JSONL rows
  - `labels`: List of entity labels to include
  - `warn_dropout`: Print warning if spans are dropped
- **Returns:** Tuple of (list of docs, skipped span count)
- **Features:**
  - Char span alignment (with "contract" mode)
  - Overlap handling with `filter_spans()`
  - Unknown label filtering

##### `evaluate(nlp, rows, labels) -> Dict[str, Any]`
- **Purpose:** Evaluate model on test set
- **Parameters:**
  - `nlp`: Trained spaCy model
  - `rows`: List of JSONL rows
  - `labels`: List of entity labels
- **Returns:** Dictionary with metrics:
  - `ents_f`: Overall F1 score
  - `ents_p`: Overall precision
  - `ents_r`: Overall recall
  - `ents_per_type`: Per-label metrics

**Command-Line Arguments:**
```bash
python train_baseline_spacy.py \
  --data ./silver_out \
  --output ./models/spacy_silver_v1 \
  --lang en \
  --epochs 20 \
  --batch_size 128 \
  --seed 13 \
  --labels DEITY PERSON PLACE \
  --use_pretrained  # Optional: use en_core_web_sm
```

**Training Loop:**
1. Initialize pipeline with tok2vec + NER
2. Register labels
3. Build training examples
4. Train for N epochs
5. Evaluate on dev after each epoch
6. Save best model (by dev F1)
7. Final evaluation on test set

---

## 3. SUPPORT UTILITIES

### 3.1 Constants

#### `code/constants.py`
**Purpose:** Centralized constants for the Bible NER pipeline

**Key Constants:**
- `NUM_CANONICAL_BOOKS`: 66
- `EXPECTED_TOTAL_VERSES`: 31,102 (KJV/NKJV standard)
- `EXPECTED_TOTAL_CHAPTERS`: 1,189
- `BOOK_CHAPTERS`: Dict[str, int] (all 66 books with chapter counts)
- `BOOK_INDEX`: Dict[str, int] (canonical order 1-66)
- `BOOK_OSIS`: Dict[str, str] (OSIS codes for STEP data)
- `OLD_TESTAMENT_BOOKS`, `NEW_TESTAMENT_BOOKS`: Separate dictionaries
- `ALIGNMENT_FALLBACK_WINDOW`: 200 (previously hardcoded)
- `DEFAULT_RANDOM_SEED`: 13 (for reproducible splits)
- `STRONGS_HEBREW_MAX`: 8,674 (H1-H8674)
- `STRONGS_GREEK_MAX`: 5,624 (G1-G5624)

**Helper Functions:**
- `validate_book_name(book_name)`: Check if valid canonical name
- `get_book_chapter_count(book_name)`: Get chapter count
- `get_book_index(book_name)`: Get canonical index (1-66)
- `get_osis_code(book_name)`: Get OSIS code
- `is_old_testament(book_name)`, `is_new_testament(book_name)`: Testament checks

---

### 3.2 Configuration

#### `code/utils/config_loader.py`
**Purpose:** Unified configuration loader with backward compatibility

**Key Functions:**

##### `load_config(profile, project_root) -> Config`
- **Purpose:** Load configuration (convenience function)
- **Parameters:**
  - `profile`: Optional profile name (e.g., "gospels_holdout")
  - `project_root`: Project root directory (auto-detected if None)
- **Returns:** Config object
- **Priority:**
  1. `config.yaml` (new unified config)
  2. `config.json` + `project.yml` + `silver_config.yml` (legacy)
  3. Default values
- **Features:**
  - Profile support (override specific settings)
  - Environment variable overrides
  - Pydantic validation (if available)

**Configuration Models (Pydantic):**
- `DatabaseConfig`: Database connection settings
- `PathsConfig`: Path configuration
- `SilverExportConfig`: Silver dataset export settings
- `LoggingConfig`: Logging configuration
- `Config`: Root configuration object

**Environment Variable Overrides:**
- `BIBLE_DATA_DIR`: Override data directory
- `BIBLE_CONCORDANCE_DB`: Override concordance.db path
- `BIBLE_GOODBOOK_DB`: Override GoodBook.db path
- `BIBLE_LOG_LEVEL`: Override log level
- `BIBLE_OUTPUT_DIR`: Override output directory

**Helper Functions:**
- `get_config_summary(config)`: Get human-readable summary

---

### 3.3 Logging

#### `code/utils/logging_config.py`
**Purpose:** Centralized logging configuration

**Key Functions:**

##### `setup_logging(name, level, log_file, console, file_level, format_string) -> logging.Logger`
- **Purpose:** Set up structured logging
- **Parameters:**
  - `name`: Logger name (use `__name__` from calling module)
  - `level`: Console log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - `log_file`: Path to log file (optional, creates rotating handler)
  - `console`: Whether to log to console (default: True)
  - `file_level`: File log level (default: DEBUG)
  - `format_string`: Custom format string (optional)
- **Returns:** Configured logger instance
- **Features:**
  - Color-coded console output
  - Rotating file handlers (max 10 MB, keep 5 backups)
  - Timestamps on all messages
  - Exception logging with stack traces

**Helper Functions:**
- `get_logger(name, level)`: Get or create a logger (convenience wrapper)
- `enable_debug_logging()`: Enable DEBUG level for all loggers
- `disable_external_loggers()`: Silence noisy third-party loggers
- `setup_script_logger(script_name, log_dir, level)`: Set up logger with automatic file logging

**Context Manager:**
- `LogLevel(logger, level)`: Temporarily change log level

**Migration from old code:**
```python
# BEFORE:
print(f"Processing {book_name}...")
print(f"ERROR: Failed to load {filename}", file=sys.stderr)

# AFTER:
logger = setup_logging(__name__)
logger.info(f"Processing {book_name}...")
logger.error(f"Failed to load {filename}")
```

---

### 3.4 Path Configuration

#### `code/utils/path_config.py`
**Purpose:** Centralized path configuration with environment variable support

**Key Class:**

##### `PathConfig`
**Purpose:** Centralized path configuration for the Bible NER pipeline

**Initialization:**
```python
paths = PathConfig(config_path=None, project_root=None)
```

**Core Directories (Properties):**
- `data_dir`: Data directory (contains databases)
- `cache_dir`: Cache directory (HTML, STEP, Strong's data)
- `output_dir`: Output directory (generated files, logs)
- `gazetteers_dir`: Gazetteers directory (entity lists)
- `entity_dir`: Entity reference files directory
- `log_dir`: Log directory

**Database Paths (Properties):**
- `goodbook_db`: Path to GoodBook.db
- `concordance_db`: Path to concordance.db
- `prodigy_db`: Path to prodigy.db

**Configuration Files (Properties):**
- `label_rules_yml`: Path to label_rules.yml
- `config_json`: Path to config.json (legacy)
- `config_yaml`: Path to unified config.yaml (new)

**Output Paths (Properties):**
- `silver_out_dir`: Silver dataset output directory
- `json_output_dir`: JSON output directory (STEP exports)
- `cleaned_dir`: Cleaned text output directory

**Cache Subdirectories (Properties):**
- `html_cache_dir`: HTML cache directory
- `strongs_cache_dir`: Strong's data cache directory
- `step_cache_dir`: STEP data cache directory

**Methods:**
- `ensure_dirs()`: Create all necessary directories
- `validate_databases()`: Check which databases exist
- `get_summary()`: Get human-readable summary

**Helper Function:**
- `get_paths(config_path)`: Get PathConfig instance (singleton-like usage)

**Priority for resolving paths:**
1. Environment variables (e.g., `BIBLE_DATA_DIR`)
2. Config file settings
3. Default relative paths from project root

---

## APPENDIX: OSIS CODES

OSIS (Open Scripture Information Standard) codes used in STEP data:

**Old Testament:**
Gen, Exo, Lev, Num, Deut, Josh, Judg, Ruth, 1Sam, 2Sam, 1Kgs, 2Kgs, 1Chr, 2Chr, Ezra, Neh, Est, Job, Psa, Prov, Eccl, Song, Isa, Jer, Lam, Ezek, Dan, Hos, Joel, Amos, Obad, Jonah, Mic, Nah, Hab, Zeph, Hag, Zech, Mal

**New Testament:**
Matt, Mark, Luke, John, Acts, Rom, 1Cor, 2Cor, Gal, Eph, Phil, Col, 1Thess, 2Thess, 1Tim, 2Tim, Titus, Phlm, Heb, Jas, 1Pet, 2Pet, 1John, 2John, 3John, Jude, Rev

---

## APPENDIX: DATABASE SCHEMA (GoodBook.db)

**Primary Tables:**
- `books`: Book metadata (id, book_name, testament, chapter_count)
- `chapters`: Chapter metadata (id, book_id, chapter_number)
- `verses`: Verse data (id, chapter_id, verse_num, text, text_plain, text_clean)
- `tokens`: Token data (id, verse_id, text, strong_norm, token_idx)
- `cross_references`: Cross-references (source_verse_id, related_verse_id)

**Indexes:**
- `ix_verses_book_chapter_verse`: Fast verse lookups
- `ix_chapters_book_chapter`: Fast chapter lookups
- `ix_xref_source`, `ix_xref_related`: Fast cross-reference queries
- `ix_tokens_verse`, `ix_tokens_strongs`: Fast token queries

---

## CHANGE LOG

**2025-11-04:**
- Initial creation of PROJECT_REPORT.md
- Documented all scraping pipelines (Bible, Strong's, STEP)
- Documented NER pipeline (silver dataset, training)
- Documented support utilities (constants, config, logging, paths)
- Added quick reference section for AI assistants
- Added detailed function documentation with parameters and return values
- Added sermon scraper documentation (SermonIndex.net)
- Integrated sermon scraper into menu_master.py and config

---

**END OF PROJECT REPORT**
