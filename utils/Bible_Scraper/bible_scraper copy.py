# BibleScraper Class Module Version 0.97 with Database Insertion
# This module defines the BibleScraper class which handles scraping Bible passages from BibleGateway.

import requests
from bs4 import BeautifulSoup
import logging
import os
import re
import sys
import json

class BibleScraper:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r") as f:
            print("📎 BibleScraper version loaded: CLEANED .97 with no response.status_code checks")
            self.config = json.load(f)

        # Load config-based paths and flags
        self.data_output_dir = self.config.get("output_dir", os.path.join("output", "data"))
        self.output_dir = self.config.get("output_dir", "output")
        self.cleaned_dir = self.config.get("cleaned_dir", self.output_dir)
        self.html_dir = self.config.get("html_dir", os.path.join(self.output_dir, "html"))
        self.json_dir = self.config.get("json_dir", os.path.join(self.output_dir, "json"))
        self.html_cache_dir = self.config.get("html_cache_dir", os.path.join(self.output_dir, "cache", "html"))
        
        self.debug_mode = self.config.get("debug_mode", True)
        self.cleanup_mode = self.config.get("cleanup_mode", True)
        self.bible_version = self.config.get("bible_version", "NKJV")
        self.save_html_copy = self.config.get("save_html_copy", True)
            
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cleaned_dir, exist_ok=True)
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)

        self.log_file = os.path.join(self.output_dir, "webverify.log")

        logging.basicConfig(
            filename=self.log_file,
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        # Dictionaries for books and chapters (keeping them as they were)
        self.OLD_TESTAMENT_BOOKS = {
            "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34,
            "Joshua": 24, "Judges": 21, "Ruth": 4, "1 Samuel": 31, "2 Samuel": 24,
            "1 Kings": 22, "2 Kings": 25, "1 Chronicles": 29, "2 Chronicles": 36, "Ezra": 10,
            "Nehemiah": 13, "Esther": 10, "Job": 42, "Psalms": 150, "Proverbs": 31,
            "Ecclesiastes": 12, "Song of Solomon": 8, "Isaiah": 66, "Jeremiah": 52,
            "Lamentations": 5, "Ezekiel": 48, "Daniel": 12, "Hosea": 14, "Joel": 3,
            "Amos": 9, "Obadiah": 1, "Jonah": 4, "Micah": 7, "Nahum": 3, "Habakkuk": 3,
            "Zephaniah": 3, "Haggai": 2, "Zechariah": 14, "Malachi": 4
        }

        self.NEW_TESTAMENT_BOOKS = {
            "Matthew": 28, "Mark": 16, "Luke": 24, "John": 21, "Acts": 28,
            "Romans": 16, "1 Corinthians": 16, "2 Corinthians": 13, "Galatians": 6,
            "Ephesians": 6, "Philippians": 4, "Colossians": 4, "1 Thessalonians": 5,
            "2 Thessalonians": 3, "1 Timothy": 6, "2 Timothy": 4, "Titus": 3,
            "Philemon": 1, "Hebrews": 13, "James": 5, "1 Peter": 5, "2 Peter": 3,
            "1 John": 5, "2 John": 1, "3 John": 1, "Jude": 1, "Revelation": 22
        }

        # Merging both dictionaries into one for easy access
        self.BOOK_CHAPTERS = {**self.OLD_TESTAMENT_BOOKS, **self.NEW_TESTAMENT_BOOKS}

        self.BOOK_INDEX = { "Genesis": 1, "Exodus": 2, "Leviticus": 3, "Numbers": 4, "Deuteronomy": 5,
                            "Joshua": 6, "Judges": 7, "Ruth": 8, "1 Samuel": 9, "2 Samuel": 10,
                            "1 Kings": 11, "2 Kings": 12, "1 Chronicles": 13, "2 Chronicles": 14,
                            "Ezra": 15, "Nehemiah": 16, "Esther": 17, "Job": 18, "Psalms": 19,
                            "Proverbs": 20, "Ecclesiastes": 21, "Song of Solomon": 22,
                            "Isaiah": 23, "Jeremiah": 24, "Lamentations": 25, "Ezekiel": 26,
                            "Daniel": 27, "Hosea": 28, "Joel": 29, "Amos": 30, "Obadiah": 31,
                            "Jonah": 32, "Micah": 33, "Nahum": 34, "Habakkuk": 35,
                            "Zephaniah": 36, "Haggai": 37, "Zechariah": 38, "Malachi": 39,
                            # New Testament
                            "Matthew": 40, "Mark": 41, "Luke": 42, "John": 43,
                            "Acts": 44, "Romans": 45, "1 Corinthians": 46, "2 Corinthians": 47,
                            "Galatians": 48, "Ephesians": 49, "Philippians": 50, "Colossians": 51,
                            "1 Thessalonians": 52, "2 Thessalonians": 53, "1 Timothy": 54, 
                            "2 Timothy": 55, "Titus": 56, "Philemon": 57, "Hebrews": 58,
                            "James": 59, "1 Peter": 60, "2 Peter": 61, "1 John": 62,
                            "2 John": 63, "3 John": 64, "Jude": 65, "Revelation": 66
                          
                            }

        self.BOOK_ABBREVIATIONS = {
                            "Genesis": ["Gen", "Gn"],
                            "Exodus": ["Ex", "Exod"],
                            "Leviticus": ["Lev", "Lv"],
                            "Numbers": ["Num", "Nm"],
                            "Deuteronomy": ["Deut", "Dt"],
                            "Joshua": ["Josh", "Jos"],
                            "Judges": ["Judg", "Jdg", "Jg", "Jdgs"],
                            "Ruth": ["Ruth", "Ru"],
                            "1 Samuel": ["1 Sam", "1Sam"],
                            "2 Samuel": ["2 Sam", "2Sam"],
                            "1 Kings": ["1 Kings", "1Kgs", "1K"],
                            "2 Kings": ["2 Kings", "2Kgs", "2K"],
                            "1 Chronicles": ["1Chron", "1Chr"],
                            "2 Chronicles": ["2Chron", "2Chr"],
                            "Ezra": ["Ezra", "Ezr"],
                            "Nehemiah": ["Neh", "Ne"],
                            "Esther": ["Esth", "Est"],
                            "Job": ["Job"],
                            "Psalms": ["Ps", "Psa", "Ps.", "Psalm"],
                            "Proverbs": ["Prov", "Prv", "Pr"],
                            "Ecclesiastes": ["Eccl", "Ecc"],
                            "Song of Solomon": ["Song", "SOS"],
                            "Isaiah": ["Isa", "Is"],
                            "Jeremiah": ["Jer", "Jr"],
                            "Lamentations": ["Lam", "La"],
                            "Ezekiel": ["Ezek", "Eze", "Ez"],
                            "Daniel": ["Dan", "Dn"],
                            "Hosea": ["Hos", "Ho"],
                            "Joel": ["Joel", "Jl"],
                            "Amos": ["Amos", "Am"],
                            "Obadiah": ["Obad", "Ob"],
                            "Jonah": ["Jonah", "Jon"],
                            "Micah": ["Mic", "Mi"],
                            "Nahum": ["Nah", "Na"],
                            "Habakkuk": ["Hab", "Hb"],
                            "Zephaniah": ["Zeph", "Zep", "Zp", "Zef"],
                            "Haggai": ["Hag", "Hg"],
                            "Zechariah": ["Zech", "Zec", "Zc"],
                            "Malachi": ["Mal", "Ml"],
                            "Matthew": ["Matt", "Mt"],
                            "Mark": ["Mark", "Mrk", "Mk"],
                            "Luke": ["Luke", "Lk"],
                            "John": ["John", "Jn"],
                            "Acts": ["Acts", "Ac"],
                            "Romans": ["Rom", "Ro", "Rm"],
                            "1 Corinthians": ["1 Cor", "1Cor"],
                            "2 Corinthians": ["2 Cor", "2Cor"],
                            "Galatians": ["Gal", "Ga"],
                            "Ephesians": ["Eph", "Ephes"],
                            "Philippians": ["Phil", "Php"],
                            "Colossians": ["Col", "Colo"],
                            "1 Thessalonians": ["1 Thess", "1Thess"],
                            "2 Thessalonians": ["2 Thess", "2Thess"],
                            "1 Timothy": ["1 Tim", "1Tim", "I Tim"],
                            "2 Timothy": ["2 Tim", "2Tim", "II Tim"],
                            "Titus": ["Titus", "Tit"],
                            "Philemon": ["Phi", "Phm", "Phlm"],
                            "Hebrews": ["Heb"],
                            "James": ["James", "Jas", "Jam"],
                            "1 Peter": ["1 Pet", "1Pet"],
                            "2 Peter": ["2 Pet", "2Pet"],
                            "1 John": ["1 John", "1John", "1 Jn", "1Jn"],
                            "2 John": ["2 John", "2John", "2 Jn", "2Jn"],
                            "3 John": ["3 John", "3John", "3 Jn", "3Jn"],
                            "Jude": ["Jude", "Jud"],
                            "Revelation": ["Rev", "Revelation", "Apocalypse"]
                        }

    def fetch_chapter_data(self, book_name, chapter_number):
        book_folder = os.path.join("cache", "html", book_name.replace(" ", "_"))
        html_path = os.path.join(book_folder, f"{book_name}_{chapter_number}.html".replace(" ", "_"))
        os.makedirs(book_folder, exist_ok=True)

        # Use cached HTML if it exists
        if os.path.exists(html_path):
            logging.info(f"Using cached HTML: {html_path}")
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        else:
            url = f"https://www.biblegateway.com/passage/?search={book_name}+{chapter_number}&version=NKJV&interface=print"
            try:
                response = requests.get(url)
                response.raise_for_status()
                html_content = response.text

                # Save HTML if enabled
                if self.config.get("save_html_copy", True):
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logging.info(f"Saved raw HTML to {html_path}")

            except requests.RequestException as e:
                logging.error(f"Network error occurred: {e}")
                return None, None
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract passage content
        passage_section = soup.find('div', class_='passage-content')
        if passage_section:
            passage_text = passage_section.get_text(separator="\n").strip()
            # Normalize the first verse number in the passage to "1"
            lines = passage_text.split("\n")
            for idx, line in enumerate(lines):
                match = re.match(r"^(\d{1,3})(\s+)(.*)", line)
                if match:
                    lines[idx] = f"1{match.group(2)}{match.group(3)}"
                    logging.debug(f"Normalized verse line: '{line}' -> '{lines[idx]}'")
                    break  # Only replace the first matching verse line
            passage_text = "\n".join(lines)
            passage_text = re.sub(r"\s+", " ", passage_text)  # Normalize whitespace
        else:
            logging.info(f"No verses found for {book_name} {chapter_number}")
            passage_text = None

        # Extract footnotes
        footnotes_section = soup.find('div', class_='footnotes')
        if footnotes_section:
            footnote_elements = footnotes_section.find_all('li')  # Find all footnote items
            formatted_footnotes = []

            for footnote in footnote_elements:
                verse_ref = footnote.find('sup')  # Extract verse reference if it exists
                footnote_text = footnote.get_text(separator=" ").strip()  # Extract full text

                if verse_ref:
                    verse = verse_ref.get_text().strip()  # Get verse number
                    footnote_text = footnote_text.replace(verse, "").strip()  # Remove reference from body
                    formatted_footnotes.append(f"{book_name} {chapter_number}:{verse} {footnote_text}")
                else:
                    formatted_footnotes.append(footnote_text)  # Fallback if no reference exists

            footnotes = "\n".join(formatted_footnotes) if formatted_footnotes else ""
        else:
            logging.info(f"No footnotes found for {book_name} {chapter_number}")
            footnotes = ""

        print(f"DEBUG: Footnotes BEFORE Combining for {book_name} {chapter_number}:\n{footnotes}")
        

        # Combine footnotes into a single variable 
        additional_info = f"Footnotes:\n{footnotes}\n".strip()
        
        return passage_text, additional_info

    def save_to_file(self, filename, book_name, chapter_number, content):
        """Append content to a given file in a structured format."""
        if content:
            with open(filename, "w", encoding="utf-8") as file:
                file.write(f"\n[{book_name} {chapter_number}]\n{content}\n\n")
            logging.info(f"Saved {book_name} {chapter_number} to {filename}")
       
    def clean_passage_text(self, book_name, chapter_number, passage_text, additional_info):
        """Cleans passage text and saves it to a file."""
        # Handle None values before processing
        if passage_text is None or passage_text.strip() == "":
            logging.error(f"Cannot clean passage text for {book_name} {chapter_number}: No data retrieved.")
            return None  # Return None so calling function knows there's an issue

        book_folder = os.path.join(self.output_dir, book_name)
        os.makedirs(book_folder, exist_ok=True)

        cleaned_passage_output = os.path.join(book_folder, f"{book_name}_data.txt".replace(" ", "_"))

        # Apply text cleaning logic
        cleaned_text = re.sub(r"Footnotes.*", "", passage_text, flags=re.DOTALL)
        cleaned_text = re.sub(r"\[\s?[a-zA-Z]{1,2}\s?\]", "", cleaned_text)
        cleaned_text = re.sub(r"\(\s?[a-zA-Z]{1,2}\s?\)", "", cleaned_text)
        cleaned_text = re.sub(r"(?<!\n)(?<=\s)(\d{1,3})(?=\s)", r"\n\1", cleaned_text)

        # Build formatted output block
        full_output = f"\n[{book_name} {chapter_number}]\n"  # newline before each chapter

        full_output += cleaned_text.strip() + "\n"  # cleaned passage block

        if additional_info.strip():
            full_output += f"\n{additional_info.strip()}"  # extra spacing around footnotes

        full_output += "\n"  # ensure one trailing newline between chapters

        # Write to file in append mode
        with open(cleaned_passage_output, "a", encoding="utf-8") as file:
            file.write(full_output)

        logging.info(f"Cleaned passage saved to {cleaned_passage_output}")
        return cleaned_passage_output

    def get_valid_chapter_number(self, book_name, chapter_number):
        """Validate a given chapter number against the known books."""
        if book_name not in self.BOOK_CHAPTERS:
            logging.warning(f"Invalid book name provided: {book_name}")
            return None

        max_chapters = self.BOOK_CHAPTERS[book_name]
        if 1 <= chapter_number <= max_chapters:
            logging.info(f"Validated chapter: {book_name} {chapter_number}")
            return chapter_number
        else:
            logging.warning(f"Invalid chapter number provided: {chapter_number} for {book_name}")
            return None

    def scrape_single_book(self, book_name):
        """Scrapes all chapters of a single book and returns cleaned data."""
        cleaned_passages = []
        for chapter in range(1, self.BOOK_CHAPTERS[book_name] + 1):
            print(f"Fetching {book_name} {chapter}...")

            passage_text, additional_info = self.fetch_chapter_data(book_name, chapter)
            if passage_text:
                cleaned_output = self.clean_passage_text(book_name, chapter, passage_text, additional_info)
                cleaned_passages.append(cleaned_output)
            else:
                logging.warning(f"Skipping {book_name} {chapter} due to missing passage text.")
        return cleaned_passages  # List of cleaned passage file paths
    
    def extract_chapter_subtitles_from_html(self, book_name, chapter_number):
        import os
        from bs4 import BeautifulSoup

        html_file = os.path.join(self.html_cache_dir, book_name, f"{book_name}_{chapter_number}.html")
        subtitles = []

        if not os.path.exists(html_file):
            return [None, None, None]

        with open(html_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        # Subtitle 1: <h2 class="psalm-book"> (e.g., BOOK ONE)
        h2_tag = soup.find("h2", class_="psalm-book")
        if h2_tag:
            subtitles.append(h2_tag.get_text(strip=True))

        # Subtitle 2: <h3 class="psalm-book"> (e.g., Psalms 1–41)
        h3_classed = soup.find("h3", class_="psalm-book")
        if h3_classed:
            subtitles.append(h3_classed.get_text(strip=True))

        # Subtitle 3: up to two <h3> tags with no class
        unclassed_h3s = [h3.get_text(strip=True) for h3 in soup.find_all("h3") if not h3.has_attr("class")]
        for h3_text in unclassed_h3s[:2]:  # Grab at most 2
            subtitles.append(h3_text)

        # Remove trailing 'About' subtitle if it appears exactly like this
        if subtitles and subtitles[-1] == 'About':
            subtitles.pop()

        # Ensure only 3 subtitles total
        while len(subtitles) < 3:
            subtitles.append(None)
        return subtitles[:3]

    def convert_to_json(self, book_name):
        import json
        import re
        import os

        input_path = os.path.join(self.data_output_dir, book_name, f"{book_name}_data.txt")
        output_path = os.path.join(self.json_dir, f"{book_name}.json")
        
        verse_pattern = re.compile(r'^(\d+)\s+(.*)')
        chapter_header_pattern = re.compile(rf"^\[{book_name} (\d+)]$")
        
        # Normalize for footnote matching (special case: Psalms uses 'Psalm')
        footnote_book_label = "Psalm" if book_name == "Psalms" else book_name
        footnote_ref_pattern = re.compile(rf"^{footnote_book_label} (\d+):(\d+)\s+(.*)")

        chapters = []
        current_chapter = None
        current_verses = []
        footnotes_by_verse = {}
        chapter_footnotes_buffer = []
        subtitle_count = 0
        in_footnotes = False

        try:
            with open(input_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Handle chapter start
                chapter_match = chapter_header_pattern.match(line)
                if chapter_match:
                    # Save previous chapter
                    if current_chapter:
                        for note_line in chapter_footnotes_buffer:
                            match = footnote_ref_pattern.match(note_line)
                            if match:
                                ch = int(match.group(1))
                                vs = int(match.group(2))
                                text = match.group(3)
                                if ch == current_chapter["chapter_number"]:
                                    footnotes_by_verse.setdefault(vs, []).append(text)

                        for verse in current_verses:
                            verse["footnotes"] = footnotes_by_verse.get(verse["verse_number"], [])

                        current_chapter["verses"] = current_verses
                        chapters.append(current_chapter)

                    # Start new chapter
                    chapter_number = int(chapter_match.group(1))
                    current_chapter = {
                        "chapter_number": chapter_number,
                        "chapter_subtitle1": None,
                        "chapter_subtitle2": None,
                        "chapter_subtitle3": None,
                    }
                    current_verses = []
                    footnotes_by_verse = {}
                    chapter_footnotes_buffer = []
                    subtitle_count = 0
                    in_footnotes = False
                    continue

                if line.startswith("Footnotes:"):
                    in_footnotes = True
                    continue

                if in_footnotes:
                    chapter_footnotes_buffer.append(line)
                    continue

                if current_chapter and subtitle_count < 3 and not verse_pattern.match(line):
                    current_chapter[f"chapter_subtitle{subtitle_count + 1}"] = line
                    subtitle_count += 1
                    continue

                match = verse_pattern.match(line)
                if match:
                    verse_number = int(match.group(1))
                    verse_text = match.group(2)
                    current_verses.append({
                        "verse_number": verse_number,
                        "text": verse_text,
                        "footnotes": []
                    })

            # Save the final chapter
            if current_chapter:
                for note_line in chapter_footnotes_buffer:
                    match = footnote_ref_pattern.match(note_line)
                    if match:
                        ch = int(match.group(1))
                        vs = int(match.group(2))
                        text = match.group(3)
                        if ch == current_chapter["chapter_number"]:
                            footnotes_by_verse.setdefault(vs, []).append(text)

                for verse in current_verses:
                    verse["footnotes"] = footnotes_by_verse.get(verse["verse_number"], [])

                current_chapter["verses"] = current_verses
                chapters.append(current_chapter)

            final_data = {
                "book": book_name,
                "chapters": chapters
            }

            os.makedirs(self.json_dir, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
                
            logging.info(f"JSON saved to {output_path}")

            # ⬇️ Automatically inject subtitles from HTML
            self.merge_html_subtitles_into_json(book_name)

        except Exception as e:
            logging.error(f"Failed to convert {book_name} to JSON: {e}")

    def batch_convert_to_json(self):
        """Batch convert all books in BOOK_CHAPTERS to JSON format using isolated instances."""
        from bible_scraper import BibleScraper  # ensure clean instance for each

        for book_name in self.BOOK_CHAPTERS:
            try:
                print(f"Converting {book_name} to JSON...")
                temp_scraper = BibleScraper()  # new scraper instance
                temp_scraper.convert_to_json(book_name)
                print(f"✅ Finished {book_name}")
            except Exception as e:
                print(f"❌ Failed to convert {book_name}: {e}")
                logging.error(f"Error converting {book_name}: {e}")

    def get_html_path(self, book_name, chapter_number):
        safe_book = book_name.replace(" ", "_")
        return os.path.join(self.html_cache_dir, safe_book, f"{safe_book}_{chapter_number}.html")

    def merge_html_subtitles_into_json(self, book_name):
        import json
        import pathlib

        SUBTITLE_IGNORE = {"About", "Help", "Our Network", "Social", "Preferences"}
        json_path = os.path.join(self.json_dir, f"{book_name}.json")
        if not os.path.exists(json_path):
            logging.error(f"JSON file not found: {json_path}")
            return
        logging.info(f"🔍 Starting subtitle merge for {book_name}...")

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for chapter in data.get("chapters", []):
                chapter_number = chapter["chapter_number"]
                html_path = self.get_html_path(book_name, chapter_number)
                if not os.path.exists(html_path):
                    logging.warning(f"Missing HTML for {book_name} {chapter_number}")
                    continue
                logging.debug(f"🔎 Checking HTML for {book_name} chapter {chapter_number}")
                with open(html_path, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f, "html.parser")

                

                # Extract subtitles (with HTML spacing preserved)
                raw_subtitles = []
                for tag in soup.find_all(['h2', 'h3']):
                    text = tag.get_text(separator=" ", strip=True)
                    if text in SUBTITLE_IGNORE:
                        continue
                    raw_subtitles.append(text)
                    if len(raw_subtitles) == 3:
                        break

                # Combine extracted subtitles and compare to existing subtitle1 (source text file)
                combined = " ".join(raw_subtitles).strip()
                original = chapter.get("chapter_subtitle1", "").strip()

                # Always split based on HTML structure, but preserve original text
                full_line = chapter.get("chapter_subtitle1", "").strip()
                part1, part2, part3 = self.split_subtitle_by_html_tags(full_line, soup)

                chapter["chapter_subtitle1"] = part1
                chapter["chapter_subtitle2"] = part2
                chapter["chapter_subtitle3"] = part3

                logging.debug(f"{book_name} {chapter_number}: Subtitles updated using HTML split guidance.")
            # Save updated JSON
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logging.info(f"Updated subtitles in JSON: {json_path}")

        except Exception as e:
            logging.error(f"Failed to merge subtitles for {book_name}: {e}")

    def split_subtitle_by_html_tags(self, full_line: str, soup) -> tuple:
        """
        Splits the full subtitle line into up to 3 parts using HTML structure for alignment.
        The HTML provides guidance; the subtitle text is only taken from the original full_line.
        """
        import re
        SUBTITLE_IGNORE = {"About", "Help", "Our Network", "Social", "Preferences"}

        subtitle_tags = []
        for tag in soup.find_all(['h2', 'h3']):
            text = tag.get_text(separator=" ", strip=True)
            if text in SUBTITLE_IGNORE:
                continue
            subtitle_tags.append(text)

        # Normalize input and subtitle tags for consistent comparison
        remaining_text = full_line.strip()
        subtitle_parts = []

        for tag_text in subtitle_tags[:2]:  # Only use first two tags for split points
            first_two_words = " ".join(remaining_text.split()[:2])
            if tag_text.startswith(first_two_words):
                # Match found – this is a valid break
                match_len = len(tag_text.split())
                matched_text = " ".join(remaining_text.split()[:match_len])
                subtitle_parts.append(matched_text)
                remaining_text = " ".join(remaining_text.split()[match_len:]).strip()
            else:
                break  # Stop splitting if alignment breaks

        if remaining_text:
            subtitle_parts.append(remaining_text)

        # Pad to 3 fields
        while len(subtitle_parts) < 3:
            subtitle_parts.append(None)

        return tuple(subtitle_parts[:3])

    def insert_json_to_db(self, json_file_or_book, db_path):
        import sqlite3
        import json
        import os

        # Allow passing a book name instead of full file path
        if not json_file_or_book.endswith(".json"):
            json_file = os.path.join(self.json_dir, f"{json_file_or_book}.json")
        else:
            json_file = json_file_or_book

        if not os.path.exists(json_file):
            logging.error(f"JSON file does not exist: {json_file}")
            return

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            book_name = data.get("book")
            chapters = data.get("chapters", [])

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            book_id = self.BOOK_INDEX.get(book_name)

            if not book_id:
                logging.error(f"Book '{book_name}' not found in BOOK_INDEX.")
                return

            cursor.execute("SELECT id FROM books WHERE id = ?", (book_id,))
            result = cursor.fetchone()

            if result:
                logging.debug(f"{book_name} already exists with ID {book_id}")
            else:
                cursor.execute("INSERT INTO books (id, book_name) VALUES (?, ?)", (book_id, book_name))
                logging.info(f"Inserted {book_name} with fixed ID {book_id}")

            for chapter in chapters:
                chapter_number = chapter["chapter_number"]
                subtitle1 = chapter.get("chapter_subtitle1")
                subtitle2 = chapter.get("chapter_subtitle2")
                subtitle3 = chapter.get("chapter_subtitle3")

                cursor.execute("""
                    INSERT INTO chapters (book_id, chapter_number, chapter_subtitle1, chapter_subtitle2, chapter_subtitle3)
                    VALUES (?, ?, ?, ?, ?)
                """, (book_id, chapter_number, subtitle1, subtitle2, subtitle3))
                chapter_id = cursor.lastrowid
                logging.debug(f"Inserted Chapter {chapter_number} (ID {chapter_id}) for {book_name}")

                for verse in chapter.get("verses", []):
                    verse_number = verse["verse_number"]
                    verse_text = verse["text"]
                    footnotes = verse.get("footnotes", [])
                    footnote_text = "; ".join(footnotes) if footnotes else None

                    cursor.execute("""
                        INSERT INTO verses (chapter_id, verse_number, text, footnote)
                        VALUES (?, ?, ?, ?)
                    """, (chapter_id, verse_number, verse_text, footnote_text))
                    logging.debug(f"Inserted {book_name} {chapter_number}:{verse_number}")

            conn.commit()
            conn.close()
            logging.info(f"✅ Successfully inserted {book_name} into {db_path}")

        except Exception as e:
            logging.error(f"❌ Failed to insert JSON into database: {e}")

    def batch_insert_all_books(self, db_path):
        for book_name in self.BOOK_CHAPTERS:
            json_file = os.path.join(self.json_dir, f"{book_name}.json")
            if os.path.exists(json_file):
                logging.info(f"Inserting {book_name} into DB...")
                self.insert_json_to_db(json_file, db_path)
            else:
                logging.warning(f"Missing JSON for {book_name} — skipping.")

    def insert_cross_references_from_file(self, file_path, db_path):
        import sqlite3
        import os

        if not os.path.exists(file_path):
            logging.error(f"Cross-reference file not found: {file_path}")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    parts = line.strip().replace('\ufeff', '').replace('\u200b', '').split('\t')
                    if len(parts) != 2:
                        logging.warning(f"Line {line_num}: Invalid format - {line.strip()}")
                        continue

                    source_ref = parts[0].strip()
                    target_ref = parts[1].strip()

                    try:
                        # Parse source
                        s_book_abbrev, s_chap, s_verse = source_ref.split('.')
                        s_book = self.resolve_abbreviation(s_book_abbrev)
                        s_chap, s_verse = int(s_chap), int(s_verse)

                        cursor.execute("""
                            SELECT verses.id FROM verses
                            JOIN chapters ON verses.chapter_id = chapters.id
                            JOIN books ON chapters.book_id = books.id
                            WHERE books.book_name = ? AND chapters.chapter_number = ? AND verses.verse_number = ?
                        """, (s_book, s_chap, s_verse))
                        src_row = cursor.fetchone()
                        if not src_row:
                            logging.warning(f"Line {line_num}: Source not found - {source_ref}")
                            continue
                        source_verse_id = src_row[0]

                        # Determine if it's a range
                        if "-" in target_ref:
                            start_ref, end_ref = target_ref.split('-')
                            related_ids = self.expand_verse_range(start_ref.strip(), end_ref.strip(), conn)
                        else:
                            t_book_abbrev, t_chap, t_verse = target_ref.strip().split('.')
                            t_book = self.resolve_abbreviation(t_book_abbrev)
                            t_chap, t_verse = int(t_chap), int(t_verse)
                            cursor.execute("""
                                SELECT verses.id FROM verses
                                JOIN chapters ON verses.chapter_id = chapters.id
                                JOIN books ON chapters.book_id = books.id
                                WHERE books.book_name = ? AND chapters.chapter_number = ? AND verses.verse_number = ?
                            """, (t_book, t_chap, t_verse))
                            row = cursor.fetchone()
                            related_ids = [row[0]] if row else []

                        for related_id in related_ids:
                            cursor.execute(
                                "INSERT INTO cross_references (source_verse_id, related_verse_id) VALUES (?, ?)",
                                (source_verse_id, related_id)
                            )
                            logging.debug(f"Linked {source_ref} → verse_id {related_id}")

                    except Exception as e:
                        logging.warning(f"Line {line_num}: Failed to insert - {line.strip()} | Error: {e}")

            conn.commit()
            conn.close()
            logging.info(f"✅ Finished inserting cross references from {file_path}")

        except Exception as e:
            logging.error(f"❌ Failed to process cross-references: {e}")

    def expand_verse_range(self, start_ref: str, end_ref: str, conn) -> list:
        """
        Expands a verse range (e.g. Prov.8.22–Prov.8.30) into a list of verse IDs.
        """
        try:
            cursor = conn.cursor()

            # Helper to parse strings like 'Prov.8.22'
            def parse_ref(ref):
                book_abbrev, chapter, verse = ref.split('.')
                full_book = self.resolve_abbreviation(book_abbrev)
                return full_book, int(chapter), int(verse)

            start_book, start_chap, start_verse = parse_ref(start_ref)
            end_book, end_chap, end_verse = parse_ref(end_ref)

            # Get starting verse ID
            cursor.execute("""
                SELECT verses.id FROM verses
                JOIN chapters ON verses.chapter_id = chapters.id
                JOIN books ON chapters.book_id = books.id
                WHERE books.book_name = ? AND chapters.chapter_number = ? AND verses.verse_number = ?
            """, (start_book, start_chap, start_verse))
            start_id_row = cursor.fetchone()

            # Get ending verse ID
            cursor.execute("""
                SELECT verses.id FROM verses
                JOIN chapters ON verses.chapter_id = chapters.id
                JOIN books ON chapters.book_id = books.id
                WHERE books.book_name = ? AND chapters.chapter_number = ? AND verses.verse_number = ?
            """, (end_book, end_chap, end_verse))
            end_id_row = cursor.fetchone()

            if not start_id_row or not end_id_row:
                logging.warning(f"Failed to locate start or end of range: {start_ref} to {end_ref}")
                return []

            start_id = start_id_row[0]
            end_id = end_id_row[0]

            # Select all verses between those two IDs (inclusive)
            cursor.execute("""
                SELECT verses.id FROM verses
                WHERE verses.id BETWEEN ? AND ?
            """, (start_id, end_id))
            results = [row[0] for row in cursor.fetchall()]
            return results

        except Exception as e:
            logging.error(f"Range expansion failed: {start_ref}–{end_ref}: {e}")
            return []

    def resolve_abbreviation(self, abbrev: str) -> str:
        normalized = abbrev.replace(".", "").replace(" ", "").lower()
        for canonical, abbrevs in self.BOOK_ABBREVIATIONS.items():
            for a in abbrevs:
                if normalized == a.replace(".", "").replace(" ", "").lower():
                    return canonical
        raise ValueError(f"Unknown book abbreviation: {abbrev}")
    
    def insert_complete_canon_from_json(self, json_data, testament, cursor):
        book = json_data["book"]  # ✅ pull book name from JSON

        for chapter_data in json_data["chapters"]:
            chapter_num = chapter_data["chapter_number"]
            for verse_data in chapter_data["verses"]:
                verse_num = verse_data["verse_number"]
                text = verse_data["text"]

                cursor.execute("""
                    INSERT INTO complete_canon (testament, book, chapter, verse, text)
                    VALUES (?, ?, ?, ?, ?)
                """, (testament, book, int(chapter_num), int(verse_num), text))

    def batch_insert_complete_canon(self, db_path):
        import sqlite3
        import os
        import json

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            for book in self.BOOK_CHAPTERS:
                json_file = os.path.join(self.json_dir, f"{book}.json")
                if not os.path.exists(json_file):
                    logging.warning(f"Missing JSON file for {book}")
                    continue

                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Determine testament
                if book in self.OLD_TESTAMENT_BOOKS:
                    testament = "Old Testament"
                elif book in self.NEW_TESTAMENT_BOOKS:
                    testament = "New Testament"
                else:
                    logging.warning(f"Unknown testament for {book}")
                    continue

                logging.info(f"Inserting {book} into complete_canon...")
                self.insert_complete_canon_from_json(data, testament, cursor)

            conn.commit()
            conn.close()
            logging.info("✅ Complete canon successfully inserted.")

        except Exception as e:
            logging.error(f"❌ Failed to batch insert canon: {e}")

    def resolve_verse_id(self, verse_id, db_path="GoodBook.db"):
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT book, chapter, verse, text FROM complete_canon WHERE id = ?
        """, (verse_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            book, chapter, verse, text = result
            return f"{book} {chapter}:{verse} – {text}"
        else:
            return f"Verse ID {verse_id} not found."

    def get_cross_references_for_verse_id(self, verse_id, db_path="GoodBook.db"):
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tgt.book, tgt.chapter, tgt.verse, tgt.text
            FROM cross_references cr
            JOIN complete_canon tgt ON cr.related_verse_id = tgt.id
            WHERE cr.source_verse_id = ?
        """, (verse_id,))
        
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return [f"No cross-references found for verse ID {verse_id}."]
        
        return [f"{book} {chapter}:{verse} – {text}" for book, chapter, verse, text in rows]

    def get_cross_references(self, verse_id_or_range, db_path="GoodBook.db", direction="forward"):
        import sqlite3
        import logging

        def parse_range(value):
            if "-" in value:
                start, end = value.split("-")
                return int(start), int(end)
            else:
                v = int(value)
                return v, v

        start_id, end_id = parse_range(verse_id_or_range)
        logging.info(f"🔍 Cross-reference lookup [{direction}] for ID(s): {start_id} to {end_id}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if direction == "forward":
            cursor.execute("""
                SELECT cr.source_verse_id, tgt.book, tgt.chapter, tgt.verse, tgt.text
                FROM cross_references cr
                JOIN complete_canon tgt ON cr.related_verse_id = tgt.id
                WHERE cr.source_verse_id BETWEEN ? AND ?
            """, (start_id, end_id))

            rows = cursor.fetchall()
            formatted = [f"[{src}] → {book} {ch}:{vs} – {txt}" for src, book, ch, vs, txt in rows]

        elif direction == "reverse":
            cursor.execute("""
                SELECT cr.related_verse_id, src.book, src.chapter, src.verse, src.text
                FROM cross_references cr
                JOIN complete_canon src ON cr.source_verse_id = src.id
                WHERE cr.related_verse_id BETWEEN ? AND ?
            """, (start_id, end_id))

            rows = cursor.fetchall()
            formatted = [f"{book} {ch}:{vs} – {txt} → [{target}]" for target, book, ch, vs, txt in rows]

        else:
            formatted = [f"Invalid direction: {direction}"]

        conn.close()

        if formatted:
            for entry in formatted:
                logging.debug(f"📘 Result: {entry}")
        else:
            logging.info(f"No cross-references found for ID(s): {verse_id_or_range}")

        return formatted or [f"No results found for ID(s) {verse_id_or_range}."]

    def main(self, book_name, chapter_number):
        book_name = self.get_valid_book_name(book_name)
        chapter_number = self.get_valid_chapter_number(book_name, chapter_number)

        if not book_name or not chapter_number:
            print(f"Error: Invalid book or chapter: {book_name} {chapter_number}.")
            logging.error(f"Invalid book or chapter: {book_name} {chapter_number}.")
            return  # Exit early

        # Fetch passage text and additional info
        passage_text, additional_info = self.fetch_chapter_data(book_name, chapter_number)

        if not passage_text:
            print(f"Error: Could not retrieve text for {book_name} {chapter_number}.")
            logging.error(f"Failed to fetch passage for {book_name} {chapter_number}.")
            return  # Exit if no passage text

        # Call clean_passage_text with correct arguments
        output_file = self.clean_passage_text(book_name, chapter_number, passage_text, additional_info)
        print(f"Processing complete. Check {output_file} for results.")
        logging.info(f"Processing completed successfully for {book_name} {chapter_number}.")
        return output_file # Return the path of the cleaned file

if __name__ == "__main__":
    # Check if enough arguments are provided
    if len(sys.argv) != 3:
        print("Usage: python bible_scraper.py <book_name> <chapter_number>")
        sys.exit(1)  # Exit if arguments are missing

    book_name = sys.argv[1]  # First argument: Book name
    try:
        chapter_number = int(sys.argv[2])  # Second argument: Chapter number (convert to int)
    except ValueError:
        print("Error: Chapter number must be an integer.")
        sys.exit(1)


    def insert_cross_references_from_file(self, file_path, db_path):
        import sqlite3
        import os
    
        if not os.path.exists(file_path):
            logging.error(f"Cross-reference file not found: {file_path}")
            return
    
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
    
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    parts = line.strip().split('\t')
                    if len(parts) != 2:
                        logging.warning(f"Line {line_num}: Invalid format - {line.strip()}")
                        continue
    
                    source_ref = parts[0].strip()
                    target_ref = parts[1].strip()
    
                    try:
                        # Parse source
                        s_book_abbrev, s_chap, s_verse = source_ref.split('.')
                        s_book = self.resolve_abbreviation(s_book_abbrev)
                        s_chap, s_verse = int(s_chap), int(s_verse)
    
                        cursor.execute("""
                            SELECT verses.id FROM verses
                            JOIN chapters ON verses.chapter_id = chapters.id
                            JOIN books ON chapters.book_id = books.id
                            WHERE books.book_name = ? AND chapters.chapter_number = ? AND verses.verse_number = ?
                        """, (s_book, s_chap, s_verse))
                        src_row = cursor.fetchone()
                        if not src_row:
                            logging.warning(f"Line {line_num}: Source not found - {source_ref}")
                            continue
                        source_verse_id = src_row[0]
    
                        # Determine if it's a range
                        if "-" in target_ref:
                            start_ref, end_ref = target_ref.split('-')
                            related_ids = self.expand_verse_range(start_ref.strip(), end_ref.strip(), conn)
                        else:
                            t_book_abbrev, t_chap, t_verse = target_ref.strip().split('.')
                            t_book = self.resolve_abbreviation(t_book_abbrev)
                            t_chap, t_verse = int(t_chap), int(t_verse)
                            cursor.execute("""
                                SELECT verses.id FROM verses
                                JOIN chapters ON verses.chapter_id = chapters.id
                                JOIN books ON chapters.book_id = books.id
                                WHERE books.book_name = ? AND chapters.chapter_number = ? AND verses.verse_number = ?
                            """, (t_book, t_chap, t_verse))
                            row = cursor.fetchone()
                            related_ids = [row[0]] if row else []
    
                        for related_id in related_ids:
                            cursor.execute(
                                "INSERT INTO cross_references (source_verse_id, related_verse_id) VALUES (?, ?)",
                                (source_verse_id, related_id)
                            )
                            logging.debug(f"Linked {source_ref} → verse_id {related_id}")
    
                    except Exception as e:
                        logging.warning(f"Line {line_num}: Failed to insert - {line.strip()} | Error: {e}")
    
            conn.commit()
            conn.close()
            logging.info(f"✅ Finished inserting cross references from {file_path}")
    
        except Exception as e:
            logging.error(f"❌ Failed to process cross-references: {e}")