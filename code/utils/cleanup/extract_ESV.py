#!/usr/bin/env python3
"""
ESV Bible Crossword Entry Extractor
FULL 3-PHASE ANALYSIS on ESV text (text_esv field)
- Phase 1: Core biblical vocabulary (2-15000 freq)
- Phase 2: Rare biblical terms (freq 1)
- Phase 3: High-frequency protected biblical terms (25-1000 freq)
"""

import sqlite3
import re
from collections import Counter, defaultdict
import random
import sys
import json
import glob
import os

# =============================================================================
# CONFIGURATION
# =============================================================================

# Database
DB_PATH = r"D:\Project_PP\projects\Bible\data\GoodBook.db"

# Output
OUTPUT_PATH = r"D:\Project_PP\Projects\Bible\Data\esv_crossword_master.txt"
REPORT_PATH = r"D:\Project_PP\Projects\Bible\esv_extraction_report.txt"
EXCLUDED_WORDS_PATH = r"D:\Project_PP\Projects\Bible\esv_excluded_words_list.txt"

# Curated entries (to protect from exclusion)
CURATED_ENTRIES_PATH = r"D:\Project_PP\projects\bible\data\*.json"

# Word pattern and length
WORD_PATTERN = r'\b[A-Za-z]{2,15}\b'
MIN_WORD_LENGTH = 2
MAX_WORD_LENGTH = 15
INCLUDE_3_LETTER = True

# Frequency ranges
PRIMARY_MIN_FREQ = 2
PRIMARY_MAX_FREQ = 15000
SECONDARY_FREQ = 1

# Phase 3: Ultra-high frequency protected words
PHASE_3_MIN_FREQ = 25
PHASE_3_MAX_FREQ = 1000

# Phase targets (1 verse per word - maximize unique vocabulary)
PHASE_1_TARGET = 150000
PHASE_2_TARGET = 25000
PHASE_3_TARGET = 10000

# Verse quality (formatting preferences for scoring - not rejection criteria)
MIN_VERSE_LENGTH = 15
MAX_VERSE_LENGTH = 150
IDEAL_VERSE_MIN = 15
IDEAL_VERSE_MAX = 250

# =============================================================================
# PROTECTED BIBLICAL TERMS
# =============================================================================

# Words that should NEVER be excluded (even if very frequent)
PROTECTED_BIBLICAL_TERMS = {
    # Major figures
    'DAVID', 'SAUL', 'MOSES', 'ABRAHAM', 'ISAAC', 'JACOB', 'JOSEPH',
    'JOSHUA', 'SAMUEL', 'SOLOMON', 'ELIJAH', 'ELISHA', 'DANIEL',
    'JESUS', 'CHRIST', 'PAUL', 'PETER', 'JOHN', 'JAMES',

    # Places
    'JERUSALEM', 'ISRAEL', 'JUDAH', 'EGYPT', 'BABYLON', 'BETHLEHEM',
    'NAZARETH', 'GALILEE', 'JORDAN', 'SINAI',

    # Theological concepts
    'GOD', 'LORD', 'SPIRIT', 'HOLY', 'HEAVEN', 'GLORY', 'GRACE',
    'RIGHTEOUS', 'COVENANT', 'FAITH', 'BLESSED', 'SANCTIFIED',

    # Biblical objects/places
    'ALTAR', 'TEMPLE', 'TABERNACLE', 'ARK', 'FIRE', 'BLOOD',

    # Key actions/concepts
    'COMMANDED', 'BLESSED', 'PROPHESY', 'SACRIFICE', 'WORSHIP',
    'PROMISED', 'ANOINTED',

    # Creation/geography
    'EARTH', 'HEAVEN', 'SEA', 'MOUNTAIN', 'WILDERNESS'
}

# Generic English words that should ALWAYS be excluded
GENERIC_ENGLISH = {
    'THE', 'AND', 'BUT', 'FOR', 'NOT', 'YOU', 'HIS', 'HER', 'YOUR',
    'THAT', 'THIS', 'THEY', 'THEM', 'THEIR', 'THOSE', 'THESE',
    'WITH', 'FROM', 'HAVE', 'HAD', 'HAS', 'WERE', 'WAS', 'ARE',
    'BEEN', 'BEING', 'WILL', 'SHALL', 'WOULD', 'SHOULD', 'COULD',
    'WHICH', 'WHAT', 'WHEN', 'WHERE', 'WHO', 'WHOM', 'WHOSE',
    'THERE', 'HERE', 'THEN', 'NOW', 'BEFORE', 'AFTER', 'UPON',
    'INTO', 'OUT', 'ALL', 'ONE', 'TWO', 'SOME', 'ANY', 'MANY',
    'MORE', 'MOST', 'OTHER', 'ANOTHER', 'SUCH', 'VERY', 'ALSO',
    'ONLY', 'JUST', 'EVEN', 'MUCH', 'WELL', 'BACK',
    'DOWN', 'OVER', 'OFF', 'THROUGH', 'BECAUSE', 'ABOUT',
    'AGAINST', 'BETWEEN', 'DURING', 'WITHOUT', 'WITHIN',
    'MAY', 'MIGHT', 'MUST', 'CAN', 'DID', 'DOES', 'DO',
    'SAYS', 'SAID', 'SAYING', 'TOLD', 'TELL', 'ASKED',
    'CAME', 'COME', 'WENT', 'GOING', 'TAKEN', 'TOOK', 'TAKE',
    'MADE', 'MAKE', 'DONE', 'DOING', 'GIVEN', 'GAVE', 'GIVE',
    'BROUGHT', 'BRING', 'PUT', 'CALLED', 'SENT', 'SEND',
    'IS', 'IT', 'IN', 'ON', 'AT', 'TO', 'BY', 'OR', 'AS', 'UP'
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def extract_words_from_text(text):
    """Extract words matching pattern from text"""
    if not text:
        return []
    words = re.findall(WORD_PATTERN, text)
    return [w.upper() for w in words]

def clean_verse_text(text):
    """Clean verse text for output"""
    if not text:
        return ""

    # Remove footnote markers
    text = re.sub(r'\[\d+\]', '', text)

    # Normalize quotes
    text = text.replace("'", "'")
    text = text.replace('"', '"')
    text = text.replace('"', '"')
    text = text.replace('—', '-')
    text = text.replace('–', '-')
    text = text.replace('â€˜', "'")
    text = text.replace('â€™', "'")
    text = text.replace('â€œ', '"')
    text = text.replace('â€', '"')

    # Normalize whitespace
    text = ' '.join(text.split())

    return text.strip()

def format_reference(book_name, chapter_num, verse_num):
    """Format scripture reference"""
    return f"{book_name} {chapter_num}:{verse_num}"

def load_curated_words(json_pattern):
    """Load words from curated JSON entries (entity type files)"""
    curated_words = set()
    json_files = glob.glob(json_pattern)

    if not json_files:
        print("  Warning: No curated JSON files found")
        return curated_words

    print(f"  Found {len(json_files)} JSON files")

    for json_file in json_files:
        try:
            filename = os.path.basename(json_file)
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                file_count = 0

                # Handle nested entity type structure
                if isinstance(data, dict):
                    for category_name, category_data in data.items():
                        if isinstance(category_data, dict):
                            for word, details in category_data.items():
                                # Extract just the word (key)
                                if ' ' in word:
                                    # Split multi-word entries and add each word
                                    parts = word.split()
                                    for part in parts:
                                        clean_part = part.strip().upper()
                                        if len(clean_part) >= 3 or clean_part in ['GO', 'OG']:
                                            curated_words.add(clean_part)
                                            file_count += 1
                                else:
                                    # Single word entry
                                    clean_word = word.strip().upper()
                                    if len(clean_word) >= 3 or clean_word in ['GO', 'OG']:
                                        curated_words.add(clean_word)
                                        file_count += 1

                print(f"    {filename}: {file_count} terms")

        except Exception as e:
            print(f"  Warning: Could not load {json_file}: {e}")

    print(f"  Total protected terms loaded: {len(curated_words):,}")
    return curated_words

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def connect_db():
    """Connect to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def build_word_frequency_map(conn):
    """Build frequency map of all words in ESV verses"""
    print("\n[1/10] Building word frequency map from ESV text...")

    cursor = conn.cursor()
    # Use text_esv field (contains ESV text)
    cursor.execute("SELECT text_esv FROM verses WHERE text_esv IS NOT NULL AND text_esv != ''")

    all_words = []
    verse_count = 0

    for (text,) in cursor:
        verse_count += 1
        if verse_count % 5000 == 0:
            print(f"  Processing verse {verse_count:,}...")

        words = extract_words_from_text(text)
        all_words.extend(words)

    word_freq = Counter(all_words)

    print(f"  Total ESV verses: {verse_count:,}")
    print(f"  Unique words: {len(word_freq):,}")

    return word_freq

def get_verses_for_word(conn, word, max_verses=50):
    """Retrieve ESV verses containing a specific word"""
    cursor = conn.cursor()

    # Use text_esv field (contains ESV text)
    query = """
        SELECT v.text_esv, b.book_name, c.chapter_number, v.verse_number
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        WHERE UPPER(v.text_esv) LIKE ?
        AND v.text_esv IS NOT NULL
        AND v.text_esv != ''
    """

    cursor.execute(query, (f'%{word}%',))
    results = cursor.fetchall()

    # Filter to only verses that actually contain the word as a complete word
    filtered = []
    pattern = r'\b' + re.escape(word) + r'\b'

    for text, book, chapter, verse in results:
        if re.search(pattern, text, re.IGNORECASE):
            filtered.append((text, book, chapter, verse))

    # Limit results
    if len(filtered) > max_verses:
        filtered = random.sample(filtered, max_verses)

    return filtered

# =============================================================================
# VERSE SCORING & SELECTION
# =============================================================================

def calculate_verse_score(verse_text, word):
    """Score a verse for quality as a crossword clue"""
    score = 100

    verse_text = clean_verse_text(verse_text)
    verse_len = len(verse_text)

    # Factor 1: Length (prefer moderate length)
    if verse_len < MIN_VERSE_LENGTH:
        score -= 50
    elif verse_len > MAX_VERSE_LENGTH:
        score -= 50
    elif IDEAL_VERSE_MIN <= verse_len <= IDEAL_VERSE_MAX:
        score += 20

    # Factor 2: Word count in verse
    pattern = r'\b' + re.escape(word) + r'\b'
    word_count = len(re.findall(pattern, verse_text, re.IGNORECASE))

    if word_count == 1:
        score += 30
    elif word_count == 2:
        score -= 10
    else:
        score -= 40

    # Factor 3: Avoid list-like verses
    comma_count = verse_text.count(',')
    if comma_count > 8:
        score -= 30
    elif comma_count > 5:
        score -= 15

    # Factor 4: Sentence structure
    if '.' in verse_text or '?' in verse_text or '!' in verse_text:
        score += 10

    # Factor 5: Direct speech
    if '"' in verse_text or '"' in verse_text:
        score += 5

    # Factor 6: Avoid verses with too many numbers
    number_count = len(re.findall(r'\d+', verse_text))
    if number_count > 5:
        score -= 20

    return score

def select_best_verses(verses_with_word, word, target_count):
    """Select the best N verses for a given word"""
    scored = []

    for text, book, chapter, verse in verses_with_word:
        score = calculate_verse_score(text, word)
        scored.append((score, text, book, chapter, verse))

    scored.sort(reverse=True)
    selected = scored[:target_count]

    return [(text, book, chapter, verse, score) for score, text, book, chapter, verse in selected]

# =============================================================================
# WORD BLANKING
# =============================================================================

def blank_word_in_verse(verse_text, word):
    """Blank the first occurrence of word in verse"""
    verse_text = clean_verse_text(verse_text)

    pattern = r'\b' + re.escape(word) + r'\b'
    match = re.search(pattern, verse_text, re.IGNORECASE)

    if not match:
        return verse_text, False

    start, end = match.span()

    # Handle possessives
    if end < len(verse_text) and verse_text[end:end+2] == "'s":
        end += 2

    blanked = verse_text[:start] + "___" + verse_text[end:]

    # Verify
    if "___" not in blanked:
        return verse_text, False

    return blanked, True

# =============================================================================
# VALIDATION
# =============================================================================

def validate_entry(word, blanked_verse, reference, exclude_list):
    """Validate entry meets quality standards"""

    # Check 1: Word length
    if len(word) < MIN_WORD_LENGTH or len(word) > MAX_WORD_LENGTH:
        if len(word) == 3 and not INCLUDE_3_LETTER:
            return False, "word_too_short"

    # Check 2: Single blank
    if blanked_verse.count("___") != 1:
        return False, "multiple_blanks"

    # Check 3: Not in exclude list
    if word.upper() in exclude_list:
        return False, "excluded_word"

    # Check 4: Reference format
    if not re.match(r'.+ \d+:\d+', reference):
        return False, "bad_reference"

    # Check 5: No weird characters
    if any(c in blanked_verse for c in ['â€', '\\x', '\x00']):
        return False, "encoding_issues"

    return True, "valid"

# =============================================================================
# PHASE EXTRACTION
# =============================================================================

def extract_phase_1(conn, word_freq, exclude_list, target):
    """Phase 1: Core biblical vocabulary (2-15000 freq)"""
    print(f"\n[3/10] PHASE 1: Core Biblical Vocabulary (freq {PRIMARY_MIN_FREQ}-{PRIMARY_MAX_FREQ})")

    phase_words = [
        w for w, f in word_freq.items()
        if PRIMARY_MIN_FREQ <= f <= PRIMARY_MAX_FREQ
        and w.upper() not in exclude_list
    ]

    print(f"  Words in range: {len(phase_words):,}")
    print(f"  Target: {target:,} entries")

    entries = []
    processed = 0

    avg_verses_per_word = 1  # Maximize unique vocabulary
    print(f"  Target verses per word: {avg_verses_per_word}")

    for word in phase_words:
        processed += 1
        if processed % 500 == 0:
            print(f"  Progress: {processed:,}/{len(phase_words):,} words ({len(entries):,} entries)")

        verses = get_verses_for_word(conn, word, max_verses=50)
        if not verses:
            continue

        best_verses = select_best_verses(verses, word, avg_verses_per_word)

        for text, book, chapter, verse_num, score in best_verses:
            blanked, success = blank_word_in_verse(text, word)
            if not success:
                continue

            reference = format_reference(book, chapter, verse_num)
            valid, reason = validate_entry(word, blanked, reference, exclude_list)

            if valid:
                entries.append({
                    'word': word.upper(),
                    'blanked': blanked,
                    'reference': reference,
                    'frequency': word_freq[word],
                    'score': score,
                    'phase': 1
                })

    print(f"  Phase 1 complete: {len(entries):,} entries")
    return entries

def extract_phase_2(conn, word_freq, exclude_list, target):
    """Phase 2: Rare biblical terms (freq 1)"""
    print(f"\n[4/10] PHASE 2: Rare Biblical Terms (freq {SECONDARY_FREQ})")

    phase_words = [
        w for w, f in word_freq.items()
        if f == SECONDARY_FREQ
        and w.upper() not in exclude_list
    ]

    print(f"  Words in range: {len(phase_words):,}")
    print(f"  Target: {target:,} entries")

    entries = []
    processed = 0

    for word in phase_words:
        processed += 1
        if processed % 500 == 0:
            print(f"  Progress: {processed:,}/{len(phase_words):,} words ({len(entries):,} entries)")

        verses = get_verses_for_word(conn, word, max_verses=1)
        if not verses:
            continue

        text, book, chapter, verse_num = verses[0]
        score = calculate_verse_score(text, word)

        blanked, success = blank_word_in_verse(text, word)
        if not success:
            continue

        reference = format_reference(book, chapter, verse_num)
        valid, reason = validate_entry(word, blanked, reference, exclude_list)

        if valid:
            entries.append({
                'word': word.upper(),
                'blanked': blanked,
                'reference': reference,
                'frequency': word_freq[word],
                'score': score,
                'phase': 2
            })

    print(f"  Phase 2 complete: {len(entries):,} entries")
    return entries

def extract_phase_3(conn, word_freq, exclude_list, protected_words, target):
    """
    Phase 3: High-Frequency PROTECTED Biblical Terms

    Extracts important biblical vocabulary that appears frequently
    (25-1000x) but was protected from exclusion because it's biblically
    significant (names, places, concepts like DAVID, JERUSALEM, FIRE, etc.)
    """
    print(f"\n[5/10] PHASE 3: High-Frequency Protected Biblical Terms (freq {PHASE_3_MIN_FREQ}-{PHASE_3_MAX_FREQ})")

    # Find protected words with medium-to-high frequency
    phase_words = [
        w for w, f in word_freq.items()
        if PHASE_3_MIN_FREQ <= f <= PHASE_3_MAX_FREQ
        and w.upper() in protected_words
    ]

    print(f"  Protected high-frequency words found: {len(phase_words):,}")
    print(f"  Target: {target:,} entries")

    if not phase_words:
        print("  No protected high-frequency words found")
        return []

    # Show some examples
    sample_words = sorted(phase_words)[:10]
    print(f"  Examples: {', '.join(sample_words)}")

    entries = []
    processed = 0

    for word in phase_words:
        processed += 1
        if processed % 50 == 0:
            print(f"  Progress: {processed:,}/{len(phase_words):,} words ({len(entries):,} entries)")

        verses_per_word = 1  # Maximize unique vocabulary
        max_verses = 10

        verses = get_verses_for_word(conn, word, max_verses=max_verses)
        if not verses:
            continue

        best_verses = select_best_verses(verses, word, verses_per_word)

        for text, book, chapter, verse_num, score in best_verses:
            blanked, success = blank_word_in_verse(text, word)
            if not success:
                continue

            reference = format_reference(book, chapter, verse_num)
            valid, reason = validate_entry(word, blanked, reference, exclude_list)

            if valid:
                entries.append({
                    'word': word.upper(),
                    'blanked': blanked,
                    'reference': reference,
                    'frequency': word_freq[word],
                    'score': score,
                    'phase': 3
                })

    print(f"  Phase 3 complete: {len(entries):,} entries")
    return entries

# =============================================================================
# OUTPUT & REPORTING
# =============================================================================

def detect_duplicates(entries):
    """Remove duplicate word+verse combinations"""
    seen = set()
    unique = []

    for entry in entries:
        key = (entry['word'], entry['reference'])
        if key not in seen:
            seen.add(key)
            unique.append(entry)

    return unique

def write_output_file(entries, output_path):
    """Write entries to output file in crossword format (one word per line with multiple clues)"""
    print(f"\n[7/10] Writing output to {output_path}")

    # Group entries by word
    word_clues = defaultdict(list)

    for entry in entries:
        word = entry['word']
        # Combine clue and reference: "blanked_verse (reference)"
        clue = f"{entry['blanked']} ({entry['reference']})"
        word_clues[word].append(clue)

    # Write one line per word with all clues tab-separated
    with open(output_path, 'w', encoding='utf-8') as f:
        for word in sorted(word_clues.keys()):
            clues = word_clues[word]
            # Format: WORD [TAB] clue1 [TAB] clue2 [TAB] clue3...
            line = word + '\t' + '\t'.join(clues) + '\n'
            f.write(line)

    unique_words = len(word_clues)
    total_clues = sum(len(clues) for clues in word_clues.values())

    print(f"  Wrote {unique_words:,} unique words with {total_clues:,} total clues")
    print(f"  Average clues per word: {total_clues/unique_words:.2f}")

def generate_report(entries, word_freq, report_path):
    """Generate detailed extraction report"""
    print(f"\n[8/10] Generating report: {report_path}")

    total_entries = len(entries)
    unique_words = len(set(e['word'] for e in entries))
    avg_per_word = total_entries / unique_words if unique_words > 0 else 0

    phase_counts = defaultdict(int)
    phase_words = defaultdict(set)
    for e in entries:
        phase_counts[e['phase']] += 1
        phase_words[e['phase']].add(e['word'])

    length_dist = defaultdict(int)
    for e in entries:
        length_dist[len(e['word'])] += 1

    freq_buckets = defaultdict(int)
    for e in entries:
        freq = e['frequency']
        if freq == 1:
            freq_buckets['1x'] += 1
        elif 2 <= freq <= 5:
            freq_buckets['2-5x'] += 1
        elif 6 <= freq <= 10:
            freq_buckets['6-10x'] += 1
        elif 11 <= freq <= 25:
            freq_buckets['11-25x'] += 1
        elif 26 <= freq <= 50:
            freq_buckets['26-50x'] += 1
        elif 51 <= freq <= 100:
            freq_buckets['51-100x'] += 1
        elif 101 <= freq <= 250:
            freq_buckets['101-250x'] += 1
        elif 251 <= freq <= 500:
            freq_buckets['251-500x'] += 1
        elif 501 <= freq <= 1000:
            freq_buckets['501-1000x'] += 1
        else:
            freq_buckets['1000+x'] += 1

    avg_clue_len = sum(len(e['blanked']) for e in entries) / total_entries if total_entries > 0 else 0

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("ESV BIBLE CROSSWORD EXTRACTION REPORT\n")
        f.write("="*70 + "\n\n")

        f.write("SUMMARY\n")
        f.write("-------\n")
        f.write(f"Total entries generated: {total_entries:,}\n")
        f.write(f"Unique words: {unique_words:,}\n")
        f.write(f"Average verses per word: {avg_per_word:.2f}\n")
        f.write(f"Average clue length: {avg_clue_len:.1f} characters\n\n")

        f.write("PHASE BREAKDOWN\n")
        f.write("---------------\n")
        f.write(f"Phase 1 (2-15000 freq):   {phase_counts[1]:7,} entries ({len(phase_words[1]):,} words)\n")
        f.write(f"Phase 2 (1 freq):         {phase_counts[2]:7,} entries ({len(phase_words[2]):,} words)\n")
        f.write(f"Phase 3 (25-1000 freq, protected): {phase_counts[3]:7,} entries ({len(phase_words[3]):,} words)\n\n")

        f.write("LENGTH DISTRIBUTION\n")
        f.write("-------------------\n")
        for length in sorted(length_dist.keys()):
            f.write(f"{length:2d} letters: {length_dist[length]:7,} entries\n")
        f.write("\n")

        f.write("FREQUENCY DISTRIBUTION\n")
        f.write("----------------------\n")
        for bucket in ['1x', '2-5x', '6-10x', '11-25x', '26-50x', '51-100x',
                       '101-250x', '251-500x', '501-1000x', '1000+x']:
            count = freq_buckets[bucket]
            if count > 0:
                f.write(f"{bucket:12s} {count:7,} entries\n")
        f.write("\n")

        f.write("SAMPLE ENTRIES\n")
        f.write("--------------\n")
        samples = random.sample(entries, min(30, len(entries)))
        for e in samples:
            f.write(f"\n{e['word']}\n")
            f.write(f"  Clue: {e['blanked']}\n")
            f.write(f"  Reference: {e['reference']}\n")
            f.write(f"  Frequency: {e['frequency']}x, Score: {e['score']}, Phase: {e['phase']}\n")

    print(f"  Report generated")

# =============================================================================
# MAIN EXTRACTION
# =============================================================================

def main():
    """Main extraction workflow"""
    print("="*70)
    print("ESV BIBLE CROSSWORD ENTRY EXTRACTOR")
    print("FULL 3-PHASE ANALYSIS on ESV text (text_esv field)")
    print("="*70)
    print(f"Database: {DB_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"No hard limit - extracting maximum quality entries\n")

    # Connect to database
    print("[0/10] Connecting to database...")
    conn = connect_db()
    print("  Connected")

    # Build word frequency map from ESV text
    word_freq = build_word_frequency_map(conn)

    # Load protected words from curated entries
    print("\n[1.5/10] Loading protected biblical terms...")
    curated_words = load_curated_words(CURATED_ENTRIES_PATH)
    protected_words = PROTECTED_BIBLICAL_TERMS | curated_words
    print(f"  Total protected terms: {len(protected_words):,}")

    # Use empty exclude list (no exclusions)
    exclude_set = set()

    print("\n[2/10] Starting extraction phases...")

    # Phase 1: Core vocabulary
    phase_1_entries = extract_phase_1(conn, word_freq, exclude_set, PHASE_1_TARGET)

    # Phase 2: Rare words
    phase_2_entries = extract_phase_2(conn, word_freq, exclude_set, PHASE_2_TARGET)

    # Phase 3: High-frequency protected biblical terms
    phase_3_entries = extract_phase_3(conn, word_freq, exclude_set, protected_words, PHASE_3_TARGET)

    # Combine all phases
    print("\n[6/10] Combining and deduplicating entries...")
    all_entries = phase_1_entries + phase_2_entries + phase_3_entries
    print(f"  Total before dedup: {len(all_entries):,}")

    unique_entries = detect_duplicates(all_entries)
    print(f"  Total after dedup: {len(unique_entries):,}")
    print(f"  Duplicates removed: {len(all_entries) - len(unique_entries):,}")

    # Shuffle for variety
    random.shuffle(unique_entries)

    print(f"  Final entry count: {len(unique_entries):,}")

    # Write output
    write_output_file(unique_entries, OUTPUT_PATH)

    # Generate report
    generate_report(unique_entries, word_freq, REPORT_PATH)

    # Close database
    conn.close()

    # Calculate final statistics
    unique_words = len(set(e['word'] for e in unique_entries))
    total_clues = len(unique_entries)

    print("\n[9/10] Extraction complete!")
    print("="*70)
    print(f"SUCCESS: {unique_words:,} unique words with {total_clues:,} total clues")
    print(f"Average clues per word: {total_clues/unique_words:.2f}")
    print(f"Output file: {OUTPUT_PATH}")
    print(f"Report file: {REPORT_PATH}")
    print("="*70)
    print("\nMASTER WORD LIST CREATED!")
    print("Format: WORD [TAB] clue1 [TAB] clue2 [TAB] ...")

if __name__ == "__main__":
    main()
