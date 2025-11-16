#!/usr/bin/env python3
"""
Bible Crossword Entry Extractor v2
FIXES:
- Smart exclude list with protected biblical terms
- Phase 3 logic fixed (uses actual excluded words)
- Verse length capped at 200 chars
- Returns actual excluded words for transparency
"""

import sqlite3
import re
from collections import Counter, defaultdict
import random
import sys
import json

# =============================================================================
# CONFIGURATION
# =============================================================================

# Database
DB_PATH = r"D:\Project_PP\Unity\Bible Crossword\GoodBook.db"

# Output
OUTPUT_PATH = r"D:\Project_PP\Unity\Bible Crossword\Assets\Crossword\CrosswordBuilder\Data\bible_crossword_v5.txt"
REPORT_PATH = r"D:\Project_PP\Unity\Bible Crossword\extraction_report_v5.txt"
EXCLUDED_WORDS_PATH = r"D:\Project_PP\Unity\Bible Crossword\excluded_words_list_v5.txt"

# Curated entries (to protect from exclusion)
CURATED_ENTRIES_PATH = r"D:\Project_PP\Unity\Bible Crossword\*.json"
# Alternative for testing: Use /mnt/user-data/uploads/*.json if files there

# Word pattern and length
WORD_PATTERN = r'\b[A-Za-z]{2,15}\b'  # CHANGED: Capture 2-15 letters
MIN_WORD_LENGTH = 2                    # CHANGED: Allow 2-letter words
MAX_WORD_LENGTH = 15
INCLUDE_3_LETTER = True                # Keep this for validation logic

# Frequency ranges
PRIMARY_MIN_FREQ = 2
PRIMARY_MAX_FREQ = 15000               # BIBLE-ONLY: Capture ALL words including THE, AND, LORD, GOD
SECONDARY_FREQ = 1  # Rare words

# Phase 3: Ultra-high frequency protected words (disabled - using Phase 1 instead)
PHASE_3_MIN_FREQ = 5001                # Not used - Phase 1 now captures all frequencies
PHASE_3_MAX_FREQ = 15000               # Not used - Phase 1 now captures all frequencies

# Phase targets (1 verse per word - maximize unique vocabulary)
PHASE_1_TARGET = 150000  # BIBLE-ONLY: Increased to extract all common words (was 100000)
PHASE_2_TARGET = 25000   # BIBLE-ONLY: Extract ALL rare words (was 15000)
PHASE_3_TARGET = 10000   # BIBLE-ONLY: Increased for high-frequency terms (was 5000)

# Verse quality (formatting preferences for scoring - not rejection criteria)
MIN_VERSE_LENGTH = 30     # Formatting preference: prefer verses at least this long
MAX_VERSE_LENGTH = 150    # Formatting preference: prefer verses no longer than this
IDEAL_VERSE_MIN = 80      # Ideal minimum for best scoring
IDEAL_VERSE_MAX = 120     # Ideal maximum for best scoring

# Generic words exclusion
# TOP_N_TO_EXCLUDE = 100  # Down from 225 (Removed because crossword builder needs these words as connectors)

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
    'ONLY', 'JUST', 'EVEN', 'MUCH', 'ALSO', 'WELL', 'BACK',
    'DOWN', 'OVER', 'OFF', 'THROUGH', 'BECAUSE', 'ABOUT',
    'AGAINST', 'BETWEEN', 'DURING', 'WITHOUT', 'WITHIN',
    'MAY', 'MIGHT', 'MUST', 'CAN', 'DID', 'DOES', 'DO',
    'SAYS', 'SAID', 'SAYING', 'TOLD', 'TELL', 'ASKED',
    'CAME', 'COME', 'WENT', 'GOING', 'TAKEN', 'TOOK', 'TAKE',
    'MADE', 'MAKE', 'DONE', 'DOING', 'GIVEN', 'GAVE', 'GIVE',
    'BROUGHT', 'BRING', 'PUT', 'CALLED', 'SENT', 'SEND'
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
    text = text.replace('â€˜', "'")  # Fix encoding
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
    import glob
    import os
    
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
                # Example: {"CATEGORY": {"word": {"default": "TYPE", "note": "..."}}}
                if isinstance(data, dict):
                    for category_name, category_data in data.items():
                        if isinstance(category_data, dict):
                            for word, details in category_data.items():
                                # Extract just the word (key)
                                # Handle multi-word entries
                                if ' ' in word:
                                    # Split multi-word entries and add each word
                                    parts = word.split()
                                    for part in parts:
                                        clean_part = part.strip().upper()
                                        # Skip very short words unless biblical
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
# SMART EXCLUDE LIST BUILDER
# =============================================================================

def build_smart_exclude_list(word_freq, top_n, protected_words):
    """
    Build exclude list intelligently:
    - Look at top N most frequent words
    - Exclude only generic English
    - Protect biblical terms (even if frequent)
    - Return actual words excluded for transparency
    
    Returns: (exclude_set, excluded_words_list, protected_count)
    """
    print(f"\n[2/10] Building smart exclude list (top {top_n} candidates)...")
    
    # Get top N most frequent words
    top_words = word_freq.most_common(top_n)
    
    exclude_set = set()
    protected_count = 0
    excluded_list = []
    
    for word, freq in top_words:
        word_upper = word.upper()
        
        # Check if protected
        if word_upper in protected_words:
            protected_count += 1
            continue
        
        # Check if generic English
        if word_upper in GENERIC_ENGLISH:
            exclude_set.add(word_upper)
            excluded_list.append((word_upper, freq, 'generic'))
            continue
        
        # Additional heuristics for generic words
        if len(word) <= 3 and word_upper not in ['GOD', 'ARK', 'SIN']:
            # Very short non-biblical words
            exclude_set.add(word_upper)
            excluded_list.append((word_upper, freq, 'short_generic'))
            continue
        
        # Words that are likely generic even if not in our list
        if word_upper in ['DAY', 'THINGS', 'THING', 'PLACE', 'TIME', 'WAY',
                          'MAN', 'MEN', 'PEOPLE', 'WORD', 'WORDS']:
            exclude_set.add(word_upper)
            excluded_list.append((word_upper, freq, 'common_generic'))
            continue
    
    print(f"  Top {top_n} candidates analyzed")
    print(f"  Protected biblical terms: {protected_count}")
    print(f"  Generic words excluded: {len(exclude_set)}")
    print(f"  Examples excluded: {', '.join(list(exclude_set)[:20])}...")
    
    # Save excluded words to file for review
    return exclude_set, excluded_list, protected_count

def save_excluded_words_report(excluded_list, output_path):
    """Save detailed report of excluded words"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("EXCLUDED WORDS REPORT\n")
        f.write("="*70 + "\n\n")
        f.write(f"Total excluded: {len(excluded_list)}\n\n")
        
        f.write("WORD                    FREQUENCY    REASON\n")
        f.write("-"*70 + "\n")
        for word, freq, reason in sorted(excluded_list, key=lambda x: -x[1]):
            f.write(f"{word:24s} {freq:8,}    {reason}\n")

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
    """Build frequency map of all words in verses"""
    print("\n[1/10] Building word frequency map...")
    
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM verses WHERE text IS NOT NULL")
    
    all_words = []
    verse_count = 0
    
    for (text,) in cursor:
        verse_count += 1
        if verse_count % 5000 == 0:
            print(f"  Processing verse {verse_count:,}...")
        
        words = extract_words_from_text(text)
        all_words.extend(words)
    
    word_freq = Counter(all_words)
    
    print(f"  Total verses: {verse_count:,}")
    print(f"  Unique words: {len(word_freq):,}")
    
    return word_freq

def get_verses_for_word(conn, word, max_verses=50):
    """Retrieve verses containing a specific word"""
    cursor = conn.cursor()
    
    query = """
        SELECT v.text, b.book_name, c.chapter_number, v.verse_number
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        WHERE UPPER(v.text) LIKE ?
        AND v.text IS NOT NULL
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
        score -= 50  # Penalize long verses more heavily
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
    
    # Check 3: Verse length (REMOVED - formatting preference only, not rejection criteria)
    # Verse length is used in scoring to PREFER ideal lengths, but we don't reject words
    # if len(blanked_verse) < MIN_VERSE_LENGTH:
    #     return False, "verse_too_short"
    # if len(blanked_verse) > MAX_VERSE_LENGTH:
    #     return False, "verse_too_long"
    
    # Check 4: Not in exclude list
    if word.upper() in exclude_list:
        return False, "excluded_word"
    
    # Check 5: Reference format
    if not re.match(r'.+ \d+:\d+', reference):
        return False, "bad_reference"
    
    # Check 6: No weird characters
    if any(c in blanked_verse for c in ['â€', '\\x', '\x00']):
        return False, "encoding_issues"
    
    return True, "valid"

# =============================================================================
# PHASE EXTRACTION
# =============================================================================

def extract_phase_1(conn, word_freq, exclude_list, target):
    """Phase 1: Core biblical vocabulary (2-500 freq)"""
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
    
    # BIBLE-ONLY: Maximize unique words, not clues per word
    # For Bible-only crosswords, we need maximum unique words.
    # One biblical clue per word is sufficient; we can add more clues later if needed.
    avg_verses_per_word = 1  # CRITICAL: Changed from 5-8 to maximize unique vocabulary
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

        # BIBLE-ONLY: Extract EVERY word in frequency range without limit
        # if len(entries) >= target:
        #     break
    
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

        # BIBLE-ONLY: Extract EVERY rare word without limit
        # if len(entries) >= target:
        #     break
    
    print(f"  Phase 2 complete: {len(entries):,} entries")
    return entries

def extract_phase_3(conn, word_freq, exclude_list, protected_words, target):
    """
    Phase 3: High-Frequency PROTECTED Biblical Terms

    Extracts important biblical vocabulary that appears frequently
    (25-1000x) but was protected from exclusion because it's biblically
    significant (names, places, concepts like DAVID, JERUSALEM, FIRE, etc.)

    Optimized based on statistical analysis to expand from 100-1000 to 25-1000,
    which increases available words from 129 to 337 (2.6x improvement).
    """
    print(f"\n[5/10] PHASE 3: High-Frequency Protected Biblical Terms (freq 25-1000)")

    # Find protected words with medium-to-high frequency
    phase_words = [
        w for w, f in word_freq.items()
        if 25 <= f <= 1000  # Optimized frequency range (was 100-1000)
        and w.upper() in protected_words  # IS protected (our curated terms)
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

        # BIBLE-ONLY: Maximize unique words, not clues per word
        # One verse per word for all frequency levels
        verses_per_word = 1  # Changed: maximize unique vocabulary
        max_verses = 10  # Still fetch 10 to pick the best one

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

        # BIBLE-ONLY: Extract EVERY protected high-frequency word without limit
        # if len(entries) >= target:
        #     break
    
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
    from collections import defaultdict
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
        f.write("BIBLE CROSSWORD EXTRACTION REPORT V2\n")
        f.write("="*70 + "\n\n")
        
        f.write("SUMMARY\n")
        f.write("-------\n")
        f.write(f"Total entries generated: {total_entries:,}\n")
        f.write(f"Unique words: {unique_words:,}\n")
        f.write(f"Average verses per word: {avg_per_word:.2f}\n")
        f.write(f"Average clue length: {avg_clue_len:.1f} characters\n\n")
        
        f.write("PHASE BREAKDOWN\n")
        f.write("---------------\n")
        f.write(f"Phase 1 (2-500 freq):     {phase_counts[1]:7,} entries ({len(phase_words[1]):,} words)\n")
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
    print("BIBLE CROSSWORD ENTRY EXTRACTOR V2")
    print("="*70)
    print(f"Database: {DB_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"No hard limit - extracting maximum quality entries\n")
    
    # Connect to database
    print("[0/10] Connecting to database...")
    conn = connect_db()
    print("  Connected")
    
    # Build word frequency map
    word_freq = build_word_frequency_map(conn)
    
    # Load protected words from curated entries
    print("\n[1.5/10] Loading protected biblical terms...")
    curated_words = load_curated_words(CURATED_ENTRIES_PATH)
    protected_words = PROTECTED_BIBLICAL_TERMS | curated_words
    print(f"  Total protected terms: {len(protected_words):,}")
    
    # Use empty exclude list since exclude functionality is removed
    exclude_set = set()
    
    print("\n[3/10] Starting extraction phases...")
    
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

if __name__ == "__main__":
    main()