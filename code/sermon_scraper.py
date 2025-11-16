#!/usr/bin/env python3
"""
SermonIndex Scraper - Download Chuck Smith sermons from SermonIndex.net

Follows the batch processing pattern established in the Bible NER project.
Features:
- Progress tracking (completed/failed sermons saved)
- Resume capability (skips already completed)
- Rate limiting (respectful 2-second delays)
- Structured output (metadata + transcripts)
- Comprehensive logging

Usage:
    python sermon_scraper.py --speaker chuck_smith
    python sermon_scraper.py --speaker chuck_smith --resume
    python sermon_scraper.py --speaker chuck_smith --max-sermons 100
"""

import argparse
import json
import time
import sys
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import requests
from datetime import datetime, timezone

# Note: This assumes utils/ is in the same parent directory
# Adjust imports if needed based on actual project structure
try:
    from utils.logging_config import setup_logging
    from utils.path_config import PathConfig
except ImportError:
    print("Warning: Could not import project utilities. Using basic logging.")
    def setup_logging(name=None, level=logging.INFO, log_file=None, console=True, file_level=None, format_string=None):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger


# ============================================================================
# CONSTANTS
# ============================================================================

SERMONINDEX_API_BASE = "http://api.sermonindex.net/audio"
GITHUB_API_BASE = "https://raw.githubusercontent.com/sermonindex/audio_api/master"

# Rate limiting - SermonIndex encourages respectful use
RATE_LIMIT_SECONDS = 2.0

# Sermon data quality thresholds
MIN_TRANSCRIPT_LENGTH = 100  # Minimum characters for a valid transcript


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
    download_url_srt: Optional[str] = None
    download_url_vtt: Optional[str] = None
    source_url: Optional[str] = None
    scraped_at: Optional[str] = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now(timezone.utc).isoformat()


# ============================================================================
# PROGRESS TRACKING
# ============================================================================

class ProgressTracker:
    """Track scraping progress with resume capability"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.progress_file = self.log_dir / "sermon_progress.json"
        self.completed_file = self.log_dir / "sermon_completed.json"
        self.failed_file = self.log_dir / "sermon_failed.json"
        
        self.completed: Set[str] = self._load_set(self.completed_file)
        self.failed: Set[str] = self._load_set(self.failed_file)
    
    def _load_set(self, path: Path) -> Set[str]:
        """Load a set from JSON file"""
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()
    
    def _save_set(self, data: Set[str], path: Path):
        """Save a set to JSON file"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(sorted(list(data)), f, indent=2)
    
    def mark_completed(self, sermon_id: str):
        """Mark a sermon as successfully scraped"""
        self.completed.add(sermon_id)
        if sermon_id in self.failed:
            self.failed.remove(sermon_id)
        self._save_set(self.completed, self.completed_file)
    
    def mark_failed(self, sermon_id: str):
        """Mark a sermon as failed"""
        self.failed.add(sermon_id)
        self._save_set(self.failed, self.failed_file)
    
    def is_completed(self, sermon_id: str) -> bool:
        """Check if sermon already scraped"""
        return sermon_id in self.completed
    
    def get_stats(self) -> Dict[str, int]:
        """Get progress statistics"""
        return {
            "completed": len(self.completed),
            "failed": len(self.failed),
            "total_processed": len(self.completed) + len(self.failed)
        }
    
    def save_progress_summary(self, stats: Dict):
        """Save overall progress summary"""
        stats["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)


# ============================================================================
# SERMONINDEX API CLIENT
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
    
    def get_speaker_index(self, use_github: bool = False) -> Dict[str, str]:
        """
        Get the speaker index (list of all speakers)
        
        Args:
            use_github: Use GitHub endpoint (more reliable) vs SermonIndex API
        
        Returns:
            Dictionary mapping speaker codes to JSON file paths
        """
        if use_github:
            url = f"{GITHUB_API_BASE}/speaker/_sermonindex.json"
        else:
            url = f"{SERMONINDEX_API_BASE}/speaker/_sermonindex.json"
        
        self.logger.info(f"Fetching speaker index from {url}")
        self._rate_limit_wait()
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to fetch speaker index: {e}")
            raise
    
    def get_speaker_sermons_html(self, speaker_code: str) -> List[Dict]:
        """
        Scrape sermon list from speaker's HTML page using Playwright for infinite scroll

        Args:
            speaker_code: Speaker code (e.g., "chuck_smith" or "chuck-smith")

        Returns:
            List of sermon dictionaries with page_id and title
        """
        # Build speaker page URL
        speaker_slug = speaker_code.replace('_', '-')
        url = f"https://www.sermonindex.net/speakers/{speaker_slug}"

        self.logger.info(f"Scraping speaker page with infinite scroll: {url}")
        self.logger.info("This may take a few minutes to load all sermons...")

        try:
            from playwright.sync_api import sync_playwright
            from bs4 import BeautifulSoup

            sermons = []

            with sync_playwright() as p:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Navigate to speaker page
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

                self.logger.info(f"Scroll complete. Parsing {current_count} sermon links...")

                # Get final HTML
                html = page.content()
                browser.close()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Find all sermon links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/sermons/' in href:
                    page_id = href.split('/sermons/')[-1].split('?')[0].split('#')[0]
                    if page_id:
                        title = link.get_text(strip=True) or "Unknown Title"
                        sermons.append({
                            'page_id': page_id,
                            'title': title,
                            'page_url': f"https://www.sermonindex.net/sermons/{page_id}"
                        })

            # Remove duplicates
            seen = set()
            unique_sermons = []
            for sermon in sermons:
                if sermon['page_id'] not in seen:
                    seen.add(sermon['page_id'])
                    unique_sermons.append(sermon)

            self.logger.info(f"Found {len(unique_sermons)} unique sermons")
            return unique_sermons

        except ImportError as e:
            self.logger.error(f"Required library missing: {e}")
            self.logger.error("Please install: pip install playwright && playwright install chromium")
            raise
        except Exception as e:
            self.logger.error(f"Failed to scrape speaker page: {e}")
            raise

    def get_speaker_sermons(self, speaker_code: str, use_github: bool = True) -> List[Dict]:
        """
        Get all sermons for a specific speaker

        Args:
            speaker_code: Speaker code (e.g., "chuck_smith")
            use_github: Use GitHub endpoint vs SermonIndex API

        Returns:
            List of sermon dictionaries
        """
        if use_github:
            url = f"{GITHUB_API_BASE}/speaker/{speaker_code}.json"
        else:
            url = f"{SERMONINDEX_API_BASE}/speaker/{speaker_code}.json"

        self.logger.info(f"Fetching sermons for {speaker_code} from {url}")
        self._rate_limit_wait()

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            sermon_refs = response.json()

            # Handle different response formats
            # 1. If it's a dict, it might be {"sermons": [...]} or similar
            if isinstance(sermon_refs, dict):
                self.logger.debug(f"Got dictionary response with keys: {list(sermon_refs.keys())}")

                # Try common key names for sermon lists
                if 'sermons' in sermon_refs:
                    sermon_list = sermon_refs['sermons']
                elif 'items' in sermon_refs:
                    sermon_list = sermon_refs['items']
                elif 'data' in sermon_refs:
                    sermon_list = sermon_refs['data']
                else:
                    # If it's a dict but not a wrapper, might be a single sermon
                    # or a dict of sermon IDs -> paths
                    # Try to get values if it looks like a mapping
                    sermon_list = list(sermon_refs.values())

            elif isinstance(sermon_refs, list):
                sermon_list = sermon_refs
            else:
                self.logger.error(f"Unexpected response type: {type(sermon_refs)}")
                return []

            # Check if we got file paths (strings) or full objects (dicts)
            if sermon_list and len(sermon_list) > 0 and isinstance(sermon_list[0], str):
                # We got file paths - need to fetch each sermon individually
                self.logger.debug(f"Got {len(sermon_list)} sermon file paths, fetching individual sermons...")
                sermons = []
                for sermon_path in sermon_list:
                    sermon_url = f"{GITHUB_API_BASE}/{sermon_path}"
                    self._rate_limit_wait()
                    try:
                        sermon_response = self.session.get(sermon_url, timeout=30)
                        sermon_response.raise_for_status()
                        sermon_data = sermon_response.json()
                        sermons.append(sermon_data)
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch sermon from {sermon_path}: {e}")
                        continue
                return sermons
            else:
                # Already got full sermon objects
                return sermon_list
        except Exception as e:
            self.logger.error(f"Failed to fetch sermons for {speaker_code}: {e}")
            raise
    
    def get_sermon_page_id(self, api_url: str) -> Optional[str]:
        """
        Extract the actual sermon page ID from the API URL page

        Args:
            api_url: API URL like http://api.sermonindex.net/SID11013

        Returns:
            Sermon page ID like "Zaklv_0cTSenMRBS" or None if not found
        """
        self._rate_limit_wait()

        try:
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()
            html = response.text

            # The page has embedded JSON with the actual sermon ID
            # Look for: "id":"Zaklv_0cTSenMRBS"
            import re
            match = re.search(r'"id"\s*:\s*"([^"]+)"', html)
            if match:
                sermon_id = match.group(1)
                self.logger.debug(f"Found sermon page ID: {sermon_id}")
                return sermon_id

            self.logger.warning(f"Could not find sermon ID in API page: {api_url}")
            return None

        except Exception as e:
            self.logger.warning(f"Failed to get sermon page ID from {api_url}: {e}")
            return None

    def scrape_sermon_page(self, sermon_page_url: str) -> Optional[Dict]:
        """
        Scrape TXT download link from sermon page

        Args:
            sermon_page_url: Full sermon page URL

        Returns:
            Dictionary with txt_download_url or None if failed
        """
        self._rate_limit_wait()

        try:
            from bs4 import BeautifulSoup

            response = self.session.get(sermon_page_url, timeout=30)
            response.raise_for_status()
            html = response.text

            soup = BeautifulSoup(html, 'html.parser')

            # Find TXT download link - look for <p class="pl-1">Download as TXT</p>
            txt_url = None
            for link in soup.find_all('a', href=True):
                # Check if link contains the "Download as TXT" text
                p_tag = link.find('p', class_='pl-1')
                if p_tag and 'Download as TXT' in p_tag.get_text():
                    txt_link = link['href']
                    if txt_link.startswith('/'):
                        txt_url = f"https://www.sermonindex.net{txt_link}"
                    else:
                        txt_url = txt_link
                    self.logger.debug(f"Found TXT download URL: {txt_url}")
                    break

            if txt_url:
                return {'txt_download_url': txt_url}
            else:
                self.logger.warning(f"No TXT download link found on: {sermon_page_url}")
                return None

        except ImportError:
            self.logger.error("BeautifulSoup is required for HTML scraping")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to scrape sermon page {sermon_page_url}: {e}")
            return None

    def scrape_transcript_from_page(self, sermon_page_url: str) -> Optional[str]:
        """
        Scrape transcript text directly from sermon page HTML

        Args:
            sermon_page_url: URL to sermon page

        Returns:
            Transcript text or None if not available
        """
        try:
            from bs4 import BeautifulSoup

            self._rate_limit_wait()
            response = self.session.get(sermon_page_url, timeout=30)
            response.raise_for_status()
            html = response.text

            soup = BeautifulSoup(html, 'html.parser')

            # Find all paragraphs with whitespace-pre-line class
            # The first one is usually the description, the second is the full transcript
            transcript_paragraphs = soup.find_all('p', class_='whitespace-pre-line')

            if len(transcript_paragraphs) >= 2:
                # The second paragraph should be the full transcript
                transcript = transcript_paragraphs[1].get_text(strip=False)

                # Validate: should be substantial and typically ends with "Amen."
                if len(transcript) > MIN_TRANSCRIPT_LENGTH:
                    self.logger.debug(f"Scraped transcript from HTML ({len(transcript)} chars)")
                    if transcript.strip().endswith('Amen.'):
                        self.logger.debug("Transcript validation: ends with 'Amen.' [OK]")
                    return transcript
                else:
                    self.logger.warning(f"Scraped transcript too short ({len(transcript)} chars)")
                    return None
            else:
                self.logger.warning(f"Could not find transcript paragraphs on page")
                return None

        except ImportError:
            self.logger.error("BeautifulSoup is required for HTML scraping")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to scrape transcript from {sermon_page_url}: {e}")
            return None

    def download_transcript_txt(self, txt_url: str) -> Optional[str]:
        """
        Download transcript TXT file directly

        Args:
            txt_url: Direct URL to TXT file

        Returns:
            Transcript text or None if not available
        """
        try:
            response = self.session.get(txt_url, timeout=30)
            response.raise_for_status()

            transcript = response.text
            if len(transcript) > MIN_TRANSCRIPT_LENGTH:
                self.logger.debug(f"Downloaded transcript ({len(transcript)} chars)")
                return transcript
            else:
                self.logger.warning(f"Transcript too short ({len(transcript)} chars)")
                return None

        except Exception as e:
            self.logger.warning(f"Failed to download transcript from {txt_url}: {e}")
            return None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def sanitize_filename(title: str, max_length: int = 100) -> str:
    """
    Convert sermon title to valid filename

    Args:
        title: Sermon title
        max_length: Maximum length for filename (default 100 chars)

    Returns:
        Sanitized filename safe for file systems
    """
    # Remove series prefix like "(People God Uses) "
    if title.startswith('(') and ')' in title:
        # Find the closing paren and skip past it
        close_paren = title.index(')')
        title = title[close_paren + 1:].strip()

    # Remove common prefixes
    title = re.sub(r'^(The Word for Today)\s*', '', title)

    # Remove extra metadata at end (play count, duration, categories)
    # Just remove everything after the pattern: numbersK numbers:numbers
    title = re.sub(r'\d+K\d+:\d+.*$', '', title)

    # Replace invalid filename characters with underscore
    title = re.sub(r'[<>:"/\\|?*]', '_', title)

    # Replace multiple spaces/underscores with single underscore
    title = re.sub(r'[\s_]+', '_', title)

    # Remove leading/trailing underscores and dashes
    title = title.strip('_-')

    # Truncate to max length
    if len(title) > max_length:
        title = title[:max_length].rstrip('_-')

    # Ensure we have something
    if not title:
        title = "sermon"

    return title


# ============================================================================
# SERMON PROCESSOR
# ============================================================================

class SermonProcessor:
    """Process and store sermon data"""
    
    def __init__(self, output_dir: Path, logger):
        self.output_dir = Path(output_dir)
        self.logger = logger
        
        # Create directory structure
        self.metadata_dir = self.output_dir / "metadata"
        self.transcripts_dir = self.output_dir / "transcripts"
        
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_sermon_data(self, raw_sermon: Dict) -> SermonMetadata:
        """
        Parse raw sermon JSON into structured metadata
        
        Args:
            raw_sermon: Raw sermon dictionary from API
        
        Returns:
            SermonMetadata object
        """
        # Extract sermon ID from URL (e.g., "http://api.sermonindex.net/SID11013" -> "SID11013")
        sermon_id = None
        url = raw_sermon.get('url', '')
        if url:
            # Extract SID from URL
            if 'SID' in url:
                sermon_id = url.split('/')[-1].split('-')[0]  # Get "SID11013" part

        # Fallback if no valid ID found
        if not sermon_id:
            sermon_id = (
                raw_sermon.get('_id') or
                raw_sermon.get('id') or
                f"sermon_{hash(raw_sermon.get('title', ''))}"
            )

        # Store the API URL directly from the 'url' field
        # We'll use this to get the actual sermon page ID later
        source_url = raw_sermon.get('url')

        # Extract series name from title if it's in parentheses
        title = raw_sermon.get('title', 'Unknown Title')
        series = None
        if title.startswith('(') and ')' in title:
            # Extract "(Series Name)" from title
            series = title[1:title.index(')')]

        metadata = SermonMetadata(
            sermon_id=str(sermon_id),
            title=title,
            speaker=raw_sermon.get('speaker_name', 'Unknown Speaker'),  # Note: speaker_name field
            scripture_refs=raw_sermon.get('scripture'),
            topics=raw_sermon.get('topic'),
            series=series,  # Extracted from title
            date=None,  # Not available in this API version
            duration=None,  # Not available in this API version
            play_count=None,  # Not available in this API version
            download_url_mp3=raw_sermon.get('download'),  # Direct MP3 download link
            download_url_txt=None,  # Must scrape from page
            download_url_pdf=None,  # Must scrape from page
            download_url_srt=None,  # Must scrape from page
            download_url_vtt=None,  # Must scrape from page
            source_url=source_url
        )
        
        return metadata
    
    def save_metadata(self, metadata: SermonMetadata):
        """Save sermon metadata as JSON"""
        output_path = self.metadata_dir / f"{metadata.sermon_id}.json"

        self.logger.info(f"Saving metadata to: {output_path}")
        self.logger.info(f"Metadata dir exists: {self.metadata_dir.exists()}")

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)

            self.logger.info(f"[OK] Saved metadata: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")
            raise
    
    def save_transcript(self, sermon_id: str, transcript: str, title: str = None):
        """
        Save sermon transcript as plain text

        Args:
            sermon_id: Unique sermon identifier (used as fallback)
            transcript: Sermon transcript text
            title: Sermon title (used to create readable filename)
        """
        if not transcript or len(transcript) < MIN_TRANSCRIPT_LENGTH:
            self.logger.warning(f"Transcript too short for {sermon_id}, skipping")
            return False

        # Create filename from title if available, otherwise use sermon_id
        if title:
            filename_base = sanitize_filename(title)
            # Append short ID to ensure uniqueness
            filename = f"{filename_base}_{sermon_id[:8]}.txt"
        else:
            filename = f"{sermon_id}.txt"

        output_path = self.transcripts_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript)

        self.logger.debug(f"Saved transcript: {output_path} ({len(transcript)} chars)")
        return True


# ============================================================================
# MAIN SCRAPER
# ============================================================================

class SermonScraper:
    """Main sermon scraper orchestrator"""
    
    def __init__(
        self,
        speaker_code: str,
        output_dir: Path,
        log_dir: Path,
        logger,
        max_sermons: Optional[int] = None,
        resume: bool = True
    ):
        self.speaker_code = speaker_code
        self.max_sermons = max_sermons
        self.resume = resume
        self.logger = logger
        
        # Initialize components
        self.client = SermonIndexClient(logger)
        self.processor = SermonProcessor(output_dir / speaker_code, logger)
        self.tracker = ProgressTracker(log_dir)
    
    def scrape_speaker(self) -> Dict:
        """
        Scrape all sermons for a speaker
        
        Returns:
            Statistics dictionary
        """
        start_time = time.time()
        
        # Get sermon list by scraping HTML
        self.logger.info(f"Scraping sermon list for {self.speaker_code}...")
        sermons = self.client.get_speaker_sermons_html(self.speaker_code)
        
        total_sermons = len(sermons)
        self.logger.info(f"Found {total_sermons} sermons for {self.speaker_code}")
        
        # Apply max limit if specified
        if self.max_sermons and total_sermons > self.max_sermons:
            sermons = sermons[:self.max_sermons]
            self.logger.info(f"Limited to first {self.max_sermons} sermons")
        
        # Process each sermon
        processed = 0
        skipped = 0
        failed = 0
        
        for idx, sermon_info in enumerate(sermons, 1):
            metadata = None
            try:
                page_id = sermon_info['page_id']
                page_url = sermon_info['page_url']

                # Check if already processed (resume capability)
                if self.resume and self.tracker.is_completed(page_id):
                    skipped += 1
                    if skipped % 10 == 0:
                        self.logger.info(f"Skipped {skipped} already-completed sermons")
                    continue

                # Log progress
                self.logger.info(f"Processing [{idx}/{len(sermons)}]: {sermon_info['title']}")

                # Construct download URLs directly from CDN pattern
                # Pattern: https://sermonindex3.b-cdn.net/{type}/S{displayRef}.{ext}
                cdn_base = "https://sermonindex3.b-cdn.net"
                file_id = f"S{page_id}"

                txt_url = f"{cdn_base}/text/{file_id}.txt"
                mp3_url = f"{cdn_base}/mp3/{file_id}.mp3"
                pdf_url = f"{cdn_base}/pdf/{file_id}.pdf"

                self.logger.debug(f"TXT URL: {txt_url}")

                # Build metadata object
                metadata = SermonMetadata(
                    sermon_id=page_id,
                    title=sermon_info['title'],
                    speaker=self.speaker_code.replace('_', ' ').replace('-', ' ').title(),
                    scripture_refs=None,
                    topics=None,
                    series=None,
                    date=None,
                    duration=None,
                    play_count=None,
                    download_url_mp3=mp3_url,
                    download_url_txt=txt_url,
                    download_url_pdf=pdf_url,
                    download_url_srt=None,
                    download_url_vtt=None,
                    source_url=page_url
                )

                # Save metadata
                self.processor.save_metadata(metadata)

                # Download transcript if TXT URL is available
                transcript_saved = False
                transcript = None

                # Try CDN download first
                if metadata.download_url_txt:
                    transcript = self.client.download_transcript_txt(metadata.download_url_txt)

                # If CDN fails, scrape from sermon page HTML
                if not transcript and metadata.source_url:
                    self.logger.info(f"CDN transcript not available, scraping from page...")
                    transcript = self.client.scrape_transcript_from_page(metadata.source_url)

                # Save transcript if we got it
                if transcript:
                    transcript_saved = self.processor.save_transcript(page_id, transcript, metadata.title)
                else:
                    self.logger.error(f"Failed to get transcript for {page_id} - neither CDN nor page scraping worked")
                
                # Mark as completed
                self.tracker.mark_completed(page_id)
                processed += 1

                # Log transcript status
                status = "with transcript" if transcript_saved else "metadata only"
                self.logger.debug(f"[OK] Completed {page_id} ({status})")
                
            except Exception as e:
                self.logger.error(f"Failed to process sermon {idx}: {e}")
                failed += 1
                if 'page_id' in locals():
                    self.tracker.mark_failed(page_id)
                continue
        
        # Calculate statistics
        elapsed_time = time.time() - start_time
        stats = {
            "speaker": self.speaker_code,
            "total_found": total_sermons,
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "elapsed_seconds": round(elapsed_time, 2),
            "elapsed_minutes": round(elapsed_time / 60, 2)
        }
        
        # Save progress summary
        self.tracker.save_progress_summary(stats)
        
        # Log summary
        self.logger.info("=" * 70)
        self.logger.info("SCRAPING COMPLETE")
        self.logger.info("=" * 70)
        self.logger.info(f"Speaker: {self.speaker_code}")
        self.logger.info(f"Total sermons found: {total_sermons}")
        self.logger.info(f"Newly processed: {processed}")
        self.logger.info(f"Skipped (already done): {skipped}")
        self.logger.info(f"Failed: {failed}")
        self.logger.info(f"Time elapsed: {stats['elapsed_minutes']:.1f} minutes")
        self.logger.info("=" * 70)
        
        return stats


# ============================================================================
# CLI INTERFACE
# ============================================================================

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Scrape sermons from SermonIndex.net",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sermon_scraper.py --speaker chuck_smith
  python sermon_scraper.py --speaker chuck_smith --max-sermons 100
  python sermon_scraper.py --speaker chuck_smith --resume --log-level DEBUG
        """
    )
    
    parser.add_argument(
        '--speaker',
        type=str,
        default='chuck_smith',
        help='Speaker code (default: chuck_smith)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='../output/sermons',
        help='Output directory (default: ../output/sermons)'
    )

    parser.add_argument(
        '--log-dir',
        type=str,
        default='../output/logs',
        help='Log directory (default: ../output/logs)'
    )
    
    parser.add_argument(
        '--max-sermons',
        type=int,
        help='Maximum number of sermons to process (default: all)'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        default=True,
        help='Resume from previous run (default: True)'
    )
    
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Start fresh (ignore previous progress)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset progress tracking (clear completed/failed lists)'
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()
    
    # Handle --no-resume flag
    resume = args.resume and not args.no_resume
    
    # Set up logging
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "sermon_scraper.log"
    
    logger = setup_logging(
        name=__name__,
        level=getattr(logging, args.log_level),
        log_file=str(log_file)
    )
    
    logger.info("=" * 70)
    logger.info("SERMONINDEX SCRAPER STARTING")
    logger.info("=" * 70)
    logger.info(f"Speaker: {args.speaker}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Log directory: {args.log_dir}")
    logger.info(f"Max sermons: {args.max_sermons or 'all'}")
    logger.info(f"Resume mode: {resume}")
    logger.info(f"Log level: {args.log_level}")
    logger.info("=" * 70)

    # Handle --reset flag
    if args.reset:
        logger.info("RESET mode: Clearing progress tracking files...")
        progress_file = log_dir / "sermon_progress.json"
        completed_file = log_dir / "sermon_completed.json"
        failed_file = log_dir / "sermon_failed.json"

        for file in [progress_file, completed_file, failed_file]:
            if file.exists():
                file.unlink()
                logger.info(f"Deleted: {file}")

        logger.info("Progress tracking reset complete!")
        logger.info("=" * 70)

    try:
        # Initialize scraper
        scraper = SermonScraper(
            speaker_code=args.speaker,
            output_dir=Path(args.output_dir),
            log_dir=log_dir,
            logger=logger,
            max_sermons=args.max_sermons,
            resume=resume
        )
        
        # Run scraping
        stats = scraper.scrape_speaker()
        
        logger.info("Scraping completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Scraping interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Scraping failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
