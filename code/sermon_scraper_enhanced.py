#!/usr/bin/env python3
"""
SermonIndex Scraper - Enhanced Version with Integrated Processing

INTEGRATED FEATURES (from CLAUDE_NOTES specs):
1. Punctuation restoration using deepmultilingualpunctuation
2. Content validation (word count, line count, structure detection)
3. Filename engineering (70-char limit with smart truncation)
4. Folder routing (transcripts/, outlines/, failed/)
5. Retry logic with alternative scraping methods
6. Comprehensive reporting (_TITLES.txt, validation reports)

Workflow:
Download → Validate → Restore Punctuation → Generate Filename → Route to Folder → Report

Usage:
    python sermon_scraper_enhanced.py --speaker chuck_smith
    python sermon_scraper_enhanced.py --speaker chuck_smith --max-sermons 100 --test-mode
"""

import argparse
import json
import time
import sys
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
import requests
from datetime import datetime, timezone

# Punctuation restoration
try:
    from deepmultilingualpunctuation import PunctuationModel  # type: ignore
    PUNCT_MODEL_AVAILABLE = True
except ImportError:
    PunctuationModel = None  # type: ignore
    print("WARNING: deepmultilingualpunctuation not installed.")
    print("Run: pip install deepmultilingualpunctuation")
    PUNCT_MODEL_AVAILABLE = False

# HTML parsing
try:
    from bs4 import BeautifulSoup  # type: ignore
    BS4_AVAILABLE = True
except ImportError:
    BeautifulSoup = None  # type: ignore
    print("WARNING: beautifulsoup4 not installed.")
    print("Run: pip install beautifulsoup4")
    BS4_AVAILABLE = False

# Browser automation
try:
    from playwright.sync_api import sync_playwright  # type: ignore
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    sync_playwright = None  # type: ignore
    print("WARNING: playwright not installed.")
    print("Run: pip install playwright && playwright install chromium")
    PLAYWRIGHT_AVAILABLE = False

# Project utilities
try:
    from utils.logging_config import setup_logging
except ImportError:
    def setup_logging(name=None, level=logging.INFO, log_file=None, console=True, file_level=None, format_string=None):
        logger = logging.getLogger(name or __name__)
        logger.setLevel(level)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger


# ============================================================================
# CONSTANTS (from SERMON_VALIDATION_SPEC.md)
# ============================================================================

# API endpoints
SERMONINDEX_API_BASE = "http://api.sermonindex.net/audio"
GITHUB_API_BASE = "https://raw.githubusercontent.com/sermonindex/audio_api/master"

# Rate limiting
RATE_LIMIT_SECONDS = 2.0

# Validation thresholds (from spec)
MIN_WORD_COUNT_TRANSCRIPT = 2400  # Minimum for transcripts
MIN_LINE_COUNT_TRANSCRIPT = 50    # Minimum lines for transcripts
MIN_CHARS_VALID = 500             # Absolute minimum to be considered valid

# Punctuation detection (from PUNCTUATION_RESTORATION_SPEC.md)
SENTENCE_ENDING_RATIO_THRESHOLD = 0.01  # Needs punctuation if ratio < 0.01

# Filename engineering (from FILENAME_ENGINEERING_SPEC.md)
MAX_FILENAME_LENGTH = 70  # Including .txt extension
MAX_TITLE_CHARS = 44      # Approximate space for title component


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class SermonMetadata:
    """Structured sermon metadata"""
    sermon_id: str
    title: str
    speaker: str
    scripture_refs: Optional[str] = None
    topics: Optional[str] = None
    series: Optional[str] = None
    date: Optional[str] = None
    duration: Optional[str] = None
    play_count: Optional[str] = None
    download_url_mp3: Optional[str] = None
    download_url_txt: Optional[str] = None
    download_url_pdf: Optional[str] = None
    source_url: Optional[str] = None
    scraped_at: Optional[str] = None

    # Validation results
    word_count: Optional[int] = None
    line_count: Optional[int] = None
    content_type: Optional[str] = None  # 'transcript', 'outline', 'unknown'
    needed_punctuation: Optional[bool] = None

    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now(timezone.utc).isoformat()


# ============================================================================
# VALIDATION SYSTEM (from SERMON_VALIDATION_SPEC.md)
# ============================================================================

class SermonValidator:
    """Validate sermon content and detect type (transcript vs outline)"""

    def __init__(self, logger):
        self.logger = logger

    def count_words(self, text: str) -> int:
        """Count words in text"""
        return len(text.split())

    def count_lines(self, text: str) -> int:
        """Count non-empty lines"""
        return len([line for line in text.split('\n') if line.strip()])

    def needs_punctuation(self, text: str) -> Tuple[bool, str]:
        """
        Detect if text lacks punctuation

        Returns:
            (needs_punctuation: bool, confidence: str)
        """
        sentence_endings = text.count('.') + text.count('?') + text.count('!')
        words = self.count_words(text)

        if words == 0:
            return (False, 'low')

        ratio = sentence_endings / words

        if ratio < 0.01:
            return (True, 'high')
        elif ratio < 0.02:
            return (True, 'medium')
        else:
            return (False, 'low')

    def detect_outline_structure(self, text: str) -> bool:
        """
        Detect if content is an outline (vs narrative transcript)

        Returns:
            True if outline-like structure detected
        """
        lines = text.split('\n')
        if len(lines) < 10:
            return False

        # Outline indicators (from spec)
        outline_patterns = [
            r'^\s*I\.',           # Roman numerals
            r'^\s*II\.',
            r'^\s*III\.',
            r'^\s*IV\.',
            r'^\s*V\.',
            r'^\s*A\.',           # Lettered points
            r'^\s*B\.',
            r'^\s*C\.',
            r'^\s*\d+\.',         # Numbered points
            r'^\s*[-•*]',         # Bullets
        ]

        matches = 0
        for line in lines:
            for pattern in outline_patterns:
                if re.match(pattern, line):
                    matches += 1
                    break

        # If > 30% of lines match outline patterns (from spec)
        ratio = matches / len(lines)
        return ratio > 0.3

    def validate(self, text: str) -> Dict:
        """
        Validate sermon content

        Returns:
            Dictionary with validation results
        """
        word_count = self.count_words(text)
        line_count = self.count_lines(text)
        is_outline = self.detect_outline_structure(text)
        needs_punct, punct_confidence = self.needs_punctuation(text)

        # Determine content type and status (from spec logic)
        if word_count < MIN_CHARS_VALID:
            status = 'fail'
            category = 'unknown'
            reason = f'Too short ({word_count} words < {MIN_CHARS_VALID} minimum)'

        elif is_outline:
            if word_count < MIN_WORD_COUNT_TRANSCRIPT:
                status = 'pass'
                category = 'outline'
                reason = 'Valid outline (structured format)'
            else:
                status = 'pass'
                category = 'transcript'
                reason = 'Large outline treated as transcript'

        elif word_count >= MIN_WORD_COUNT_TRANSCRIPT and line_count >= MIN_LINE_COUNT_TRANSCRIPT:
            status = 'pass'
            category = 'transcript'
            reason = 'Valid transcript'

        elif line_count < 10 and word_count > 1000:
            status = 'retry'
            category = 'unknown'
            reason = 'Single-line file needs fixing'

        elif 2000 <= word_count < MIN_WORD_COUNT_TRANSCRIPT:
            status = 'manual_review'
            category = 'transcript'
            reason = 'Borderline word count (manual review recommended)'

        else:
            status = 'retry'
            category = 'unknown'
            reason = f'Failed validation (words={word_count}, lines={line_count})'

        return {
            'status': status,
            'category': category,
            'reason': reason,
            'word_count': word_count,
            'line_count': line_count,
            'is_outline': is_outline,
            'needs_punctuation': needs_punct,
            'punct_confidence': punct_confidence
        }


# ============================================================================
# PUNCTUATION RESTORATION (from PUNCTUATION_RESTORATION_SPEC.md)
# ============================================================================

class PunctuationRestorer:
    """Restore punctuation using deepmultilingualpunctuation"""

    def __init__(self, logger):
        self.logger = logger
        self.model = None

        if PUNCT_MODEL_AVAILABLE:
            try:
                self.logger.info("Loading punctuation model (this may take a moment)...")
                self.model = PunctuationModel()
                self.logger.info("Punctuation model loaded successfully")
            except Exception as e:
                self.logger.error(f"Failed to load punctuation model: {e}")
                self.model = None
        else:
            self.logger.warning("Punctuation model not available - skipping punctuation restoration")

    def restore(self, text: str) -> Optional[str]:
        """
        Restore punctuation in text

        Returns:
            Punctuated text or None if failed
        """
        if not self.model:
            return None

        try:
            punctuated = self.model.restore_punctuation(text)
            return punctuated
        except Exception as e:
            self.logger.error(f"Punctuation restoration failed: {e}")
            return None


# ============================================================================
# FILENAME ENGINEERING (from FILENAME_ENGINEERING_SPEC.md)
# ============================================================================

class FilenameGenerator:
    """Generate clean, readable filenames with 70-char limit"""

    # Words to remove for truncation (from spec)
    ARTICLES = ['a', 'an', 'the']
    PREPOSITIONS = ['of', 'in', 'on', 'at', 'by', 'for', 'with', 'from', 'to']
    CONNECTING = ['and', 'or', 'but']

    def __init__(self, logger):
        self.logger = logger

    def sanitize_component(self, text: str) -> str:
        """Remove/replace special characters for filename safety"""
        # Replace problematic chars
        replacements = {
            '/': '-',
            ':': '-',
            '&': 'and',
            ' ': '_'
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Remove invalid chars
        remove_chars = ['"', "'", '?', '!', '<', '>', '|', '*', '(', ')']
        for char in remove_chars:
            text = text.replace(char, '')

        return text

    def remove_non_essential_words(self, title: str) -> str:
        """Remove articles, prepositions, connecting words"""
        words = title.split('_')
        remove_words = self.ARTICLES + self.PREPOSITIONS + self.CONNECTING

        # Keep first and last words, filter middle
        if len(words) <= 2:
            return title

        filtered = [words[0]]  # Always keep first
        for word in words[1:-1]:
            if word.lower() not in remove_words:
                filtered.append(word)
        filtered.append(words[-1])  # Always keep last

        return '_'.join(filtered)

    def truncate_title(self, title: str, max_chars: int) -> str:
        """Truncate title to fit max_chars, breaking at word boundaries"""
        if len(title) <= max_chars:
            return title

        # Remove non-essential words first
        title = self.remove_non_essential_words(title)

        if len(title) <= max_chars:
            return title

        # Truncate at word boundaries
        words = title.split('_')
        result = words[0]  # Keep first word

        for word in words[1:-1]:
            if len(result + '_' + word) < max_chars - len(words[-1]) - 1:
                result += '_' + word

        # Add last word if space allows
        if len(result + '_' + words[-1]) <= max_chars:
            result += '_' + words[-1]

        return result

    def format_scripture_ref(self, scripture: Optional[str]) -> str:
        """Format scripture reference (e.g., 'Genesis 24:1-67' -> 'GEN_24')"""
        if not scripture:
            return "TOPIC"

        # Bible book abbreviations (from spec)
        book_abbrevs = {
            'genesis': 'GEN', 'exodus': 'EXO', 'leviticus': 'LEV', 'numbers': 'NUM',
            'deuteronomy': 'DEU', 'joshua': 'JOS', 'judges': 'JDG', 'ruth': 'RUT',
            '1 samuel': '1SA', '2 samuel': '2SA', '1 kings': '1KI', '2 kings': '2KI',
            '1 chronicles': '1CH', '2 chronicles': '2CH', 'ezra': 'EZR', 'nehemiah': 'NEH',
            'esther': 'EST', 'job': 'JOB', 'psalms': 'PSA', 'proverbs': 'PRO',
            'ecclesiastes': 'ECC', 'song of solomon': 'SNG', 'isaiah': 'ISA',
            'jeremiah': 'JER', 'lamentations': 'LAM', 'ezekiel': 'EZK', 'daniel': 'DAN',
            'hosea': 'HOS', 'joel': 'JOL', 'amos': 'AMO', 'obadiah': 'OBA',
            'jonah': 'JON', 'micah': 'MIC', 'nahum': 'NAH', 'habakkuk': 'HAB',
            'zephaniah': 'ZEP', 'haggai': 'HAG', 'zechariah': 'ZEC', 'malachi': 'MAL',
            'matthew': 'MAT', 'mark': 'MRK', 'luke': 'LUK', 'john': 'JHN',
            'acts': 'ACT', 'romans': 'ROM', '1 corinthians': '1CO', '2 corinthians': '2CO',
            'galatians': 'GAL', 'ephesians': 'EPH', 'philippians': 'PHP', 'colossians': 'COL',
            '1 thessalonians': '1TH', '2 thessalonians': '2TH', '1 timothy': '1TI',
            '2 timothy': '2TI', 'titus': 'TIT', 'philemon': 'PHM', 'hebrews': 'HEB',
            'james': 'JAS', '1 peter': '1PE', '2 peter': '2PE', '1 john': '1JN',
            '2 john': '2JN', '3 john': '3JN', 'jude': 'JUD', 'revelation': 'REV'
        }

        # Parse scripture reference
        scripture_lower = scripture.lower().strip()

        for book_name, abbrev in book_abbrevs.items():
            if scripture_lower.startswith(book_name):
                # Extract chapter (first number after book name)
                chapter_match = re.search(r'(\d+)', scripture)
                if chapter_match:
                    chapter = chapter_match.group(1)
                    return f"{abbrev}_{chapter}"
                return abbrev

        # Fallback
        return "REF"

    def generate(self, title: str, scripture: Optional[str], sermon_id: str) -> str:
        """
        Generate filename with 70-char limit

        Format: {title}_{ref}_{id}.txt

        Returns:
            Filename string
        """
        # Sanitize title
        title_clean = self.sanitize_component(title)

        # Format components
        ref = self.format_scripture_ref(scripture)
        sermon_id_short = sermon_id[:12] if len(sermon_id) > 12 else sermon_id

        # Calculate available space for title
        used_space = len(ref) + len(sermon_id_short) + 6  # +6 for underscores and .txt
        available = MAX_FILENAME_LENGTH - used_space

        # Truncate title to fit
        title_truncated = self.truncate_title(title_clean, available)

        # Assemble filename
        filename = f"{title_truncated}_{ref}_{sermon_id_short}.txt"

        # Final length check
        if len(filename) > MAX_FILENAME_LENGTH:
            # Emergency truncation
            excess = len(filename) - MAX_FILENAME_LENGTH
            title_truncated = title_truncated[:-excess]
            filename = f"{title_truncated}_{ref}_{sermon_id_short}.txt"

        return filename


# ============================================================================
# SERMON PROCESSOR (Enhanced with validation & routing)
# ============================================================================

class SermonProcessor:
    """Process and store sermon data with validation and folder routing"""

    def __init__(self, output_dir: Path, logger):
        self.output_dir = Path(output_dir)
        self.logger = logger

        # Create folder structure (from spec)
        self.transcripts_dir = self.output_dir / "transcripts"
        self.transcripts_raw_dir = self.output_dir / "transcripts_raw"
        self.outlines_dir = self.output_dir / "outlines"
        self.failed_dir = self.output_dir / "failed"
        self.validation_reports_dir = self.output_dir / "validation_reports"
        self.metadata_dir = self.output_dir / "metadata"

        for folder in [self.transcripts_dir, self.transcripts_raw_dir, self.outlines_dir,
                      self.failed_dir, self.validation_reports_dir, self.metadata_dir]:
            folder.mkdir(parents=True, exist_ok=True)

        # Initialize processing components
        self.validator = SermonValidator(logger)
        self.punctuator = PunctuationRestorer(logger)
        self.filename_gen = FilenameGenerator(logger)

        # Track results for reporting
        self.results = {
            'transcripts': [],
            'outlines': [],
            'failed': [],
            'punctuation_restored': 0,
            'punctuation_skipped': 0
        }

    def process_sermon(self, sermon_id: str, title: str, scripture: Optional[str],
                      transcript: str, metadata: SermonMetadata) -> Dict:
        """
        Complete sermon processing pipeline

        Workflow:
        1. Validate content
        2. Detect punctuation needs
        3. Restore punctuation if needed
        4. Generate filename
        5. Route to appropriate folder
        6. Save files
        7. Return results

        Returns:
            Processing results dictionary
        """
        # Step 1: Validate
        validation = self.validator.validate(transcript)

        self.logger.info(f"Validation: {validation['status']} - {validation['category']} - {validation['reason']}")
        self.logger.info(f"  Words: {validation['word_count']}, Lines: {validation['line_count']}")

        # Update metadata with validation results
        metadata.word_count = validation['word_count']
        metadata.line_count = validation['line_count']
        metadata.content_type = validation['category']
        metadata.needed_punctuation = validation['needs_punctuation']

        # Step 2: Handle validation failures
        if validation['status'] == 'fail':
            # Save to failed folder
            filename = f"{sermon_id}_FAILED.txt"
            self.save_to_folder(self.failed_dir, filename, transcript)
            self.results['failed'].append({
                'sermon_id': sermon_id,
                'title': title,
                'reason': validation['reason'],
                'word_count': validation['word_count']
            })
            return {
                'status': 'failed',
                'reason': validation['reason'],
                'folder': 'failed'
            }

        # Step 3: Determine if needs punctuation restoration
        processed_transcript = transcript

        if validation['needs_punctuation'] and validation['punct_confidence'] in ['high', 'medium']:
            self.logger.info("Restoring punctuation...")
            # Save raw version as backup
            self.save_raw_backup(sermon_id, transcript, title)

            # Restore punctuation
            punctuated = self.punctuator.restore(transcript)
            if punctuated:
                processed_transcript = punctuated
                self.results['punctuation_restored'] += 1
                self.logger.info(f"[OK] Punctuation restored ({len(punctuated)} chars)")
            else:
                self.logger.warning("Punctuation restoration failed, using original")
                self.results['punctuation_skipped'] += 1
        else:
            self.results['punctuation_skipped'] += 1

        # Step 4: Generate filename
        filename = self.filename_gen.generate(title, scripture, sermon_id)
        self.logger.info(f"Generated filename: {filename} ({len(filename)} chars)")

        # Step 5: Route to appropriate folder
        if validation['category'] == 'transcript':
            target_folder = self.transcripts_dir
            folder_name = 'transcripts'
        elif validation['category'] == 'outline':
            target_folder = self.outlines_dir
            folder_name = 'outlines'
        else:
            target_folder = self.failed_dir
            folder_name = 'failed'

        # Step 6: Save files
        self.save_to_folder(target_folder, filename, processed_transcript)
        self.save_metadata(metadata)

        # Step 7: Track results
        result_entry = {
            'filename': filename,
            'title': title,
            'sermon_id': sermon_id,
            'word_count': validation['word_count'],
            'line_count': validation['line_count'],
            'punctuation_restored': validation['needs_punctuation']
        }

        if validation['category'] == 'transcript':
            self.results['transcripts'].append(result_entry)
        elif validation['category'] == 'outline':
            self.results['outlines'].append(result_entry)

        self.logger.info(f"[OK] Saved to {folder_name}/{filename}")

        return {
            'status': 'success',
            'filename': filename,
            'folder': folder_name,
            'validation': validation
        }

    def save_to_folder(self, folder: Path, filename: str, content: str):
        """Save content to specified folder"""
        output_path = folder / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def save_raw_backup(self, sermon_id: str, content: str, title: str):
        """Save raw unpunctuated version as backup"""
        filename = f"{sermon_id}_raw.txt"
        self.save_to_folder(self.transcripts_raw_dir, filename, content)

    def save_metadata(self, metadata: SermonMetadata):
        """Save sermon metadata as JSON"""
        output_path = self.metadata_dir / f"{metadata.sermon_id}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)

    def generate_titles_mapping(self):
        """Generate _TITLES.txt files for each folder"""
        for folder, results_list in [
            (self.transcripts_dir, self.results['transcripts']),
            (self.outlines_dir, self.results['outlines'])
        ]:
            if not results_list:
                continue

            titles_file = folder / "_TITLES.txt"
            with open(titles_file, 'w', encoding='utf-8') as f:
                for entry in sorted(results_list, key=lambda x: x['filename']):
                    f.write(f"{entry['filename']}|{entry['title']}|{entry['sermon_id']}\n")

            self.logger.info(f"Generated {titles_file}")

    def generate_validation_report(self, speaker: str, stats: Dict):
        """Generate validation report (from spec format)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.validation_reports_dir / f"validation_report_{timestamp}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("SERMON VALIDATION REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Speaker: {speaker}\n")
            f.write("="*70 + "\n\n")

            # Summary
            total = len(self.results['transcripts']) + len(self.results['outlines']) + len(self.results['failed'])
            f.write("SUMMARY:\n")
            f.write("--------\n")
            f.write(f"Total Processed: {total}\n")
            if total > 0:
                f.write(f"Transcripts: {len(self.results['transcripts'])} ({len(self.results['transcripts'])/total*100:.1f}%)\n")
                f.write(f"Outlines: {len(self.results['outlines'])} ({len(self.results['outlines'])/total*100:.1f}%)\n")
                f.write(f"Failed: {len(self.results['failed'])} ({len(self.results['failed'])/total*100:.1f}%)\n")
            else:
                f.write(f"Transcripts: {len(self.results['transcripts'])} (0.0%)\n")
                f.write(f"Outlines: {len(self.results['outlines'])} (0.0%)\n")
                f.write(f"Failed: {len(self.results['failed'])} (0.0%)\n")
            f.write(f"Punctuation Restored: {self.results['punctuation_restored']}\n")
            f.write(f"Punctuation Skipped: {self.results['punctuation_skipped']}\n\n")

            # Transcripts
            f.write("TRANSCRIPTS (in transcripts/ folder):\n")
            f.write("--------------------------------------\n")
            for entry in sorted(self.results['transcripts'], key=lambda x: x['filename'])[:50]:
                f.write(f"{entry['filename']} [{entry['word_count']} words]\n")
            if len(self.results['transcripts']) > 50:
                f.write(f"... and {len(self.results['transcripts']) - 50} more\n")
            f.write("\n")

            # Outlines
            f.write("OUTLINES (in outlines/ folder):\n")
            f.write("--------------------------------\n")
            for entry in sorted(self.results['outlines'], key=lambda x: x['filename'])[:50]:
                f.write(f"{entry['filename']} [{entry['word_count']} words]\n")
            if len(self.results['outlines']) > 50:
                f.write(f"... and {len(self.results['outlines']) - 50} more\n")
            f.write("\n")

            # Failed
            if self.results['failed']:
                f.write("FAILED (in failed/ folder - NEEDS MANUAL REVIEW):\n")
                f.write("--------------------------------------------------\n")
                for entry in sorted(self.results['failed'], key=lambda x: x['sermon_id']):
                    f.write(f"{entry['sermon_id']} - {entry['reason']}\n")
                f.write("\n")

            f.write("="*70 + "\n")
            f.write("END REPORT\n")

        self.logger.info(f"Generated validation report: {report_file}")
        return report_file


# ============================================================================
# SERMONINDEX API CLIENT (from original scraper)
# ============================================================================

class SermonIndexClient:
    """Client for SermonIndex API with rate limiting"""

    def __init__(self, logger, rate_limit: float = RATE_LIMIT_SECONDS):
        self.logger = logger
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BibleCompanionProject/1.0 (Educational/Research; Respectful Bot)'
        })

    def _rate_limit_wait(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            wait_time = self.rate_limit - elapsed
            time.sleep(wait_time)
        self.last_request_time = time.time()

    def get_speaker_sermons_html(self, speaker_code: str) -> List[Dict]:
        """
        Scrape sermon list from speaker's HTML page using Playwright

        Returns:
            List of sermon dictionaries with page_id and title
        """
        if not PLAYWRIGHT_AVAILABLE or not BS4_AVAILABLE:
            raise RuntimeError("Playwright and BeautifulSoup4 required for scraping")

        speaker_slug = speaker_code.replace('_', '-')
        url = f"https://www.sermonindex.net/speakers/{speaker_slug}"

        self.logger.info(f"Scraping speaker page: {url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)

            self.logger.info("Page loaded, starting infinite scroll...")

            # Scroll to load all sermons (aggressive scrolling for infinite scroll)
            prev_count = 0
            no_change_count = 0
            max_no_change = 10  # Stop after 10 scrolls with no new content
            scroll_attempts = 0
            max_scrolls = 200  # Safety limit to prevent infinite loops

            while scroll_attempts < max_scrolls:
                scroll_attempts += 1

                # Get current sermon count (count unique sermon links)
                current_count = page.locator('a[href*="/sermons/"]').count()

                if current_count > prev_count:
                    self.logger.info(f"Loaded {current_count} sermons... (scroll #{scroll_attempts})")
                    prev_count = current_count
                    no_change_count = 0
                else:
                    no_change_count += 1

                # Stop if no new content after multiple scrolls
                if no_change_count >= max_no_change:
                    self.logger.info(f"No new sermons after {max_no_change} scrolls, stopping.")
                    break

                # Multiple scroll strategies
                # 1. Scroll to bottom
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)

                # 2. Scroll up slightly then back down (triggers some lazy loaders)
                page.evaluate("window.scrollBy(0, -100)")
                page.wait_for_timeout(200)
                page.evaluate("window.scrollBy(0, 200)")

                # 3. Wait for network to be idle (new content loading)
                try:
                    page.wait_for_load_state("networkidle", timeout=3000)
                except:
                    pass  # Timeout is fine, just continue

            self.logger.info(f"Scrolling complete after {scroll_attempts} attempts.")

            html = page.content()
            browser.close()

        # Parse HTML
        if not BS4_AVAILABLE:
            raise RuntimeError("BeautifulSoup4 not available for HTML parsing")
        
        soup = BeautifulSoup(html, 'html.parser')
        sermons = []
        seen = set()

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if isinstance(href, str) and '/sermons/' in href:
                page_id = href.split('/sermons/')[-1].split('?')[0].split('#')[0]
                if page_id and page_id not in seen:
                    seen.add(page_id)
                    title = link.get_text(strip=True) or "Unknown Title"
                    sermons.append({
                        'page_id': page_id,
                        'title': title,
                        'page_url': f"https://www.sermonindex.net/sermons/{page_id}"
                    })

        self.logger.info(f"Found {len(sermons)} unique sermons")
        return sermons

    def scrape_transcript_from_page(self, sermon_page_url: str) -> Optional[str]:
        """Scrape transcript from HTML (PRIMARY METHOD)"""
        if not BS4_AVAILABLE:
            self.logger.warning("BeautifulSoup4 not available, skipping page scraping")
            return None

        try:
            self._rate_limit_wait()
            response = self.session.get(sermon_page_url, timeout=30)
            response.raise_for_status()

            if not BS4_AVAILABLE or BeautifulSoup is None:
                raise RuntimeError("BeautifulSoup4 not available")

            soup = BeautifulSoup(response.text, 'html.parser')
            transcript_paragraphs = soup.find_all('p', class_='whitespace-pre-line')

            if len(transcript_paragraphs) >= 2:
                transcript = transcript_paragraphs[1].get_text(strip=False)
                if len(transcript) > MIN_CHARS_VALID:
                    return transcript

            return None
        except Exception as e:
            self.logger.warning(f"Failed to scrape from page: {e}")
            return None

    def download_transcript_txt(self, txt_url: str) -> Optional[str]:
        """Download transcript from CDN (ALTERNATIVE METHOD)"""
        try:
            self._rate_limit_wait()
            response = self.session.get(txt_url, timeout=30)
            response.raise_for_status()

            transcript = response.text
            if len(transcript) > MIN_CHARS_VALID:
                return transcript

            return None
        except Exception as e:
            self.logger.debug(f"CDN download failed: {e}")
            return None


# ============================================================================
# PROGRESS TRACKING
# ============================================================================

class ProgressTracker:
    """Track scraping progress"""

    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.completed_file = self.log_dir / "sermon_completed.json"
        self.failed_file = self.log_dir / "sermon_failed.json"

        self.completed: Set[str] = self._load_set(self.completed_file)
        self.failed: Set[str] = self._load_set(self.failed_file)

    def _load_set(self, path: Path) -> Set[str]:
        if path.exists():
            try:
                with open(path, 'r') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()

    def _save_set(self, data: Set[str], path: Path):
        with open(path, 'w') as f:
            json.dump(sorted(list(data)), f, indent=2)

    def mark_completed(self, sermon_id: str):
        self.completed.add(sermon_id)
        self._save_set(self.completed, self.completed_file)

    def mark_failed(self, sermon_id: str):
        self.failed.add(sermon_id)
        self._save_set(self.failed, self.failed_file)

    def is_completed(self, sermon_id: str) -> bool:
        return sermon_id in self.completed


# ============================================================================
# MAIN SCRAPER (Enhanced)
# ============================================================================

class EnhancedSermonScraper:
    """Enhanced sermon scraper with integrated processing pipeline"""

    def __init__(self, speaker_code: str, output_dir: Path, log_dir: Path,
                 logger, max_sermons: Optional[int] = None, resume: bool = True):
        self.speaker_code = speaker_code
        self.max_sermons = max_sermons
        self.resume = resume
        self.logger = logger

        # Initialize components
        self.client = SermonIndexClient(logger)
        self.processor = SermonProcessor(output_dir / speaker_code, logger)
        self.tracker = ProgressTracker(log_dir)

    def scrape_speaker(self) -> Dict:
        """Scrape all sermons with integrated processing"""
        start_time = time.time()

        # Get sermon list
        self.logger.info(f"Fetching sermon list for {self.speaker_code}...")
        sermons = self.client.get_speaker_sermons_html(self.speaker_code)

        total_sermons = len(sermons)
        self.logger.info(f"Found {total_sermons} sermons")

        if self.max_sermons:
            sermons = sermons[:self.max_sermons]
            self.logger.info(f"Limited to {self.max_sermons} sermons")

        # Process each sermon
        processed = 0
        skipped = 0
        failed = 0

        for idx, sermon_info in enumerate(sermons, 1):
            try:
                page_id = sermon_info['page_id']

                # Resume capability
                if self.resume and self.tracker.is_completed(page_id):
                    skipped += 1
                    continue

                self.logger.info(f"\n[{idx}/{len(sermons)}] Processing: {sermon_info['title']}")

                # Get transcript (try page scraping first, then CDN)
                transcript = self.client.scrape_transcript_from_page(sermon_info['page_url'])

                if not transcript:
                    # Try CDN as fallback
                    cdn_txt_url = f"https://sermonindex3.b-cdn.net/text/S{page_id}.txt"
                    transcript = self.client.download_transcript_txt(cdn_txt_url)

                if not transcript:
                    self.logger.error(f"Failed to get transcript for {page_id}")
                    self.tracker.mark_failed(page_id)
                    failed += 1
                    continue

                # Create metadata
                metadata = SermonMetadata(
                    sermon_id=page_id,
                    title=sermon_info['title'],
                    speaker=self.speaker_code.replace('_', ' ').title(),
                    source_url=sermon_info['page_url']
                )

                # Process sermon (validate, punctuate, route, save)
                result = self.processor.process_sermon(
                    page_id,
                    sermon_info['title'],
                    None,  # scripture ref not available from HTML scraping
                    transcript,
                    metadata
                )

                if result['status'] == 'success':
                    self.tracker.mark_completed(page_id)
                    processed += 1
                else:
                    self.tracker.mark_failed(page_id)
                    failed += 1

            except Exception as e:
                self.logger.error(f"Error processing sermon {idx}: {e}", exc_info=True)
                failed += 1
                continue

        # Generate reports
        self.processor.generate_titles_mapping()

        elapsed = time.time() - start_time
        stats = {
            'speaker': self.speaker_code,
            'total_found': total_sermons,
            'processed': processed,
            'skipped': skipped,
            'failed': failed,
            'elapsed_minutes': round(elapsed / 60, 2)
        }

        report_file = self.processor.generate_validation_report(self.speaker_code, stats)

        # Log summary
        self.logger.info("\n" + "="*70)
        self.logger.info("SCRAPING COMPLETE")
        self.logger.info("="*70)
        self.logger.info(f"Total sermons: {total_sermons}")
        self.logger.info(f"Processed: {processed}")
        self.logger.info(f"Skipped: {skipped}")
        self.logger.info(f"Failed: {failed}")
        self.logger.info(f"Time: {stats['elapsed_minutes']:.1f} minutes")
        self.logger.info(f"Report: {report_file}")
        self.logger.info("="*70)

        return stats


# ============================================================================
# CLI INTERFACE
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="Enhanced SermonIndex Scraper")

    parser.add_argument('--speaker', default='chuck_smith', help='Speaker code')
    parser.add_argument('--output-dir', default='../output/sermons', help='Output directory')
    parser.add_argument('--log-dir', default='../output/logs', help='Log directory')
    parser.add_argument('--max-sermons', type=int, help='Max sermons to process')
    parser.add_argument('--resume', action='store_true', default=True, help='Resume from previous run')
    parser.add_argument('--no-resume', action='store_true', help='Start fresh')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    parser.add_argument('--test-mode', action='store_true', help='Test mode (process 10 sermons)')

    return parser.parse_args()


def main():
    args = parse_args()

    # Test mode
    if args.test_mode:
        args.max_sermons = 10
        print("TEST MODE: Processing 10 sermons only")

    # Setup logging
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "sermon_scraper_enhanced.log"

    logger = setup_logging(
        name=__name__,
        level=getattr(logging, args.log_level),
        log_file=str(log_file)
    )

    logger.info("="*70)
    logger.info("ENHANCED SERMONINDEX SCRAPER")
    logger.info("="*70)
    logger.info(f"Speaker: {args.speaker}")
    logger.info(f"Max sermons: {args.max_sermons or 'all'}")
    logger.info(f"Resume: {args.resume and not args.no_resume}")
    logger.info("="*70)

    try:
        scraper = EnhancedSermonScraper(
            speaker_code=args.speaker,
            output_dir=Path(args.output_dir),
            log_dir=log_dir,
            logger=logger,
            max_sermons=args.max_sermons,
            resume=args.resume and not args.no_resume
        )

        stats = scraper.scrape_speaker()

        logger.info("Scraping completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
