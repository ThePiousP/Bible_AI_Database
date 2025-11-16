#!/usr/bin/env python3
"""
Comprehensive Analysis of GoodBook.db for Crossword Entry Extraction
Analyzes word frequency, distribution, and context to design optimal extraction strategy
"""

import sqlite3
import re
from collections import Counter, defaultdict
import random

# Database configuration
DB_PATH = r"D:\Project_PP\projects\bible\data\GoodBook.db"
WORD_PATTERN = r'\b[A-Za-z]{3,15}\b'

# Frequency buckets for analysis
FREQUENCY_BUCKETS = [
    (1, 1, "1x"),
    (2, 5, "2-5x"),
    (6, 10, "6-10x"),
    (11, 25, "11-25x"),
    (26, 50, "26-50x"),
    (51, 100, "51-100x"),
    (101, 250, "101-250x"),
    (251, 500, "251-500x"),
    (501, 1000, "501-1000x"),
    (1001, 2000, "1001-2000x"),
    (2001, float('inf'), "2001+x")
]

def connect_db():
    """Connect to the database"""
    return sqlite3.connect(DB_PATH)

def extract_words_from_text(text):
    """Extract words matching the pattern from text"""
    if not text:
        return []
    words = re.findall(WORD_PATTERN, text)
    return [w.upper() for w in words]

def analysis_1_basic_extraction(conn):
    """
    ANALYSIS 1: BASIC WORD EXTRACTION
    Extract all unique words and build frequency counter
    """
    print("\n" + "="*70)
    print("ANALYSIS 1: BASIC WORD EXTRACTION")
    print("="*70)

    cursor = conn.cursor()
    cursor.execute("SELECT text FROM verses WHERE text IS NOT NULL")

    all_words = []
    verse_count = 0

    for (text,) in cursor:
        verse_count += 1
        words = extract_words_from_text(text)
        all_words.extend(words)

    word_freq = Counter(all_words)
    unique_words = len(word_freq)
    total_words = len(all_words)

    print(f"Total verses: {verse_count:,}")
    print(f"Total words extracted: {total_words:,}")
    print(f"Unique words (3-15 letters): {unique_words:,}")

    return word_freq, verse_count, total_words

def analysis_2_frequency_distribution(word_freq):
    """
    ANALYSIS 2: FREQUENCY DISTRIBUTION ANALYSIS
    Analyze how words are distributed across frequency buckets
    """
    print("\n" + "="*70)
    print("ANALYSIS 2: FREQUENCY DISTRIBUTION")
    print("="*70)

    # Group words by frequency buckets
    bucket_counts = {}
    for min_freq, max_freq, label in FREQUENCY_BUCKETS:
        count = sum(1 for w, f in word_freq.items() if min_freq <= f <= max_freq)
        bucket_counts[label] = count

    total_unique = len(word_freq)

    for min_freq, max_freq, label in FREQUENCY_BUCKETS:
        count = bucket_counts[label]
        percentage = (count / total_unique * 100) if total_unique > 0 else 0
        print(f"{label:12s} {count:6,} words ({percentage:5.1f}%)")

    return bucket_counts

def analysis_3_length_distribution(word_freq):
    """
    ANALYSIS 3: WORD LENGTH DISTRIBUTION
    Analyze distribution by word length
    """
    print("\n" + "="*70)
    print("ANALYSIS 3: WORD LENGTH DISTRIBUTION")
    print("="*70)

    length_dist = defaultdict(int)
    for word in word_freq.keys():
        length_dist[len(word)] += 1

    for length in range(3, 16):
        count = length_dist.get(length, 0)
        print(f"{length:2d} letters: {count:6,} words")

    # Summary for crossword-friendly lengths
    ideal_count = sum(length_dist[l] for l in range(4, 13))
    print(f"\nCrossword-ideal (4-12 letters): {ideal_count:,} words")

    return dict(length_dist)

def analysis_4_common_words(word_freq):
    """
    ANALYSIS 4: COMMON WORD FILTER ANALYSIS
    Identify most frequent words (likely generic English)
    """
    print("\n" + "="*70)
    print("ANALYSIS 4: TOP 200 MOST FREQUENT WORDS")
    print("="*70)

    top_words = word_freq.most_common(200)

    for i, (word, count) in enumerate(top_words, 1):
        print(f"{i:3d}. {word:20s} {count:8,} occurrences")

    # Calculate percentage of total occurrences
    total_occurrences = sum(word_freq.values())
    top_200_occurrences = sum(count for _, count in top_words)
    percentage = (top_200_occurrences / total_occurrences * 100)

    print(f"\nTop 200 words represent: {percentage:.1f}% of total occurrences")

    # Suggest generic words to exclude (very subjective, but based on common English)
    generic_candidates = [word for word, _ in top_words[:50]]
    print(f"\nGeneric English candidates (top 50): {', '.join(generic_candidates[:20])}...")

    return top_words

def analysis_5_verse_context_sampling(conn, word_freq):
    """
    ANALYSIS 5: VERSE CONTEXT SAMPLING
    Show sample verses for words in different frequency ranges
    """
    print("\n" + "="*70)
    print("ANALYSIS 5: SAMPLE VERSES BY FREQUENCY")
    print("="*70)

    cursor = conn.cursor()

    # Sample frequency ranges
    sample_ranges = [
        (1, 1, "1x (Rare/Unique)"),
        (2, 5, "2-5x"),
        (6, 10, "6-10x"),
        (51, 100, "51-100x"),
        (501, 1000, "501-1000x")
    ]

    for min_freq, max_freq, label in sample_ranges:
        print(f"\nFREQUENCY: {label}")
        print("-" * 70)

        # Get words in this range
        words_in_range = [w for w, f in word_freq.items() if min_freq <= f <= max_freq]

        if not words_in_range:
            print("No words in this range")
            continue

        # Sample up to 5 words
        sample_words = random.sample(words_in_range, min(5, len(words_in_range)))

        for word in sample_words:
            freq = word_freq[word]

            # Find a verse containing this word
            cursor.execute("""
                SELECT text FROM verses
                WHERE UPPER(text) LIKE ?
                LIMIT 1
            """, (f'%{word}%',))

            result = cursor.fetchone()
            if result:
                verse_text = result[0]
                # Truncate if too long
                if len(verse_text) > 200:
                    verse_text = verse_text[:200] + "..."

                print(f"\nWord: {word} ({freq} occurrence{'s' if freq > 1 else ''})")
                print(f"Verse: {verse_text}")

def analysis_6_reference_extraction(conn, word_freq):
    """
    ANALYSIS 6: BOOK/CHAPTER/VERSE REFERENCE EXTRACTION
    Test ability to generate proper citations
    """
    print("\n" + "="*70)
    print("ANALYSIS 6: REFERENCE EXTRACTION TEST")
    print("="*70)

    cursor = conn.cursor()

    # Get schema info to understand table structure
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\nAvailable tables: {', '.join(tables)}")

    # Check verses table structure
    cursor.execute("PRAGMA table_info(verses)")
    verses_columns = [row[1] for row in cursor.fetchall()]
    print(f"Verses columns: {', '.join(verses_columns)}")

    # Check for related tables
    if 'chapters' in tables:
        cursor.execute("PRAGMA table_info(chapters)")
        chapters_columns = [row[1] for row in cursor.fetchall()]
        print(f"Chapters columns: {', '.join(chapters_columns)}")

    if 'books' in tables:
        cursor.execute("PRAGMA table_info(books)")
        books_columns = [row[1] for row in cursor.fetchall()]
        print(f"Books columns: {', '.join(books_columns)}")

    # Try to construct full references
    print("\nSample references with verse text:")
    print("-" * 70)

    # Attempt to join tables and get references
    try:
        query = """
            SELECT v.text, b.book_name, c.chapter_number, v.verse_number
            FROM verses v
            LEFT JOIN chapters c ON v.chapter_id = c.id
            LEFT JOIN books b ON c.book_id = b.id
            WHERE v.text IS NOT NULL
            LIMIT 10
        """
        cursor.execute(query)

        for verse_text, book_name, chapter_num, verse_num in cursor:
            if verse_text and book_name:
                # Extract a sample word from the verse
                words = extract_words_from_text(verse_text)
                if words:
                    sample_word = words[0]

                    # Create blanked version
                    blanked = re.sub(r'\b' + re.escape(sample_word) + r'\b', '___', verse_text, flags=re.IGNORECASE)

                    # Truncate if needed
                    if len(verse_text) > 150:
                        verse_text = verse_text[:150] + "..."
                        blanked = blanked[:150] + "..."

                    print(f"\nWord: {sample_word}")
                    print(f"Reference: {book_name} {chapter_num}:{verse_num}")
                    print(f"Original: {verse_text}")
                    print(f"Blanked: {blanked}")

    except Exception as e:
        print(f"Error joining tables: {e}")
        print("Will need to investigate table relationships further")

def analysis_7_duplicate_words(conn):
    """
    ANALYSIS 7: DUPLICATE WORD/VERSE ANALYSIS
    Find words that appear multiple times in the same verse
    """
    print("\n" + "="*70)
    print("ANALYSIS 7: DUPLICATE WORD IN VERSE ANALYSIS")
    print("="*70)

    cursor = conn.cursor()
    cursor.execute("SELECT text FROM verses WHERE text IS NOT NULL")

    duplicate_cases = []

    for (text,) in cursor:
        words = extract_words_from_text(text)
        word_counts = Counter(words)

        # Find words appearing 2+ times in this verse
        for word, count in word_counts.items():
            if count >= 2:
                duplicate_cases.append((word, count, text))

    print(f"Total duplicate cases found: {len(duplicate_cases):,}")

    # Group by word to see which words have this issue
    words_with_duplicates = set(word for word, _, _ in duplicate_cases)
    print(f"Unique words appearing 2+ times in a single verse: {len(words_with_duplicates):,}")

    # Show examples
    print("\nExamples:")
    print("-" * 70)
    for word, count, text in duplicate_cases[:10]:
        if len(text) > 150:
            text = text[:150] + "..."
        print(f"\n{word} appears {count}x in verse:")
        print(f"{text}")

def analysis_8_capacity_projection(word_freq, bucket_counts, length_dist):
    """
    ANALYSIS 8: EXTRACTION CAPACITY PROJECTION
    Estimate how many quality entries we can generate
    """
    print("\n" + "="*70)
    print("ANALYSIS 8: EXTRACTION CAPACITY PROJECTION")
    print("="*70)

    total_unique = len(word_freq)

    # Calculate various filters
    top_200_generic = 200
    only_once = bucket_counts.get("1x", 0)
    very_high_freq = bucket_counts.get("2001+x", 0)

    # Middle range (good biblical vocabulary)
    middle_range_words = sum(
        bucket_counts.get(label, 0)
        for _, _, label in FREQUENCY_BUCKETS
        if label in ["2-5x", "6-10x", "11-25x", "26-50x", "51-100x", "101-250x", "251-500x"]
    )

    print(f"Total unique words (3-15 letters):           {total_unique:8,}")
    print(f"Generic words to exclude (top 200):          {top_200_generic:8,}")
    print(f"Words appearing only 1x (low priority):      {only_once:8,}")
    print(f"Words appearing 2000+ (too generic):         {very_high_freq:8,}")
    print(f"\nRemaining biblical vocabulary (2-500x):      {middle_range_words:8,}")

    # Length analysis
    print(f"\nBy length (4-12 letters ideal):")
    ideal_length = sum(length_dist.get(l, 0) for l in range(4, 13))
    print(f"  Total 4-12 letter words:                   {ideal_length:8,}")

    # Projection for 50K target
    print(f"\nTarget: 50,000 entries")
    print("="*70)

    if middle_range_words > 0:
        verses_per_word_needed = 50000 / middle_range_words
        print(f"Strategy:")
        print(f"  - Primary extraction range: 2-500 occurrences")
        print(f"  - Available words in range: {middle_range_words:,}")
        print(f"  - Verses needed per word (avg): {verses_per_word_needed:.1f}")

        # Calculate average occurrences for words in range
        words_in_range = [w for w, f in word_freq.items() if 2 <= f <= 500]
        if words_in_range:
            avg_occurrences = sum(word_freq[w] for w in words_in_range) / len(words_in_range)
            print(f"  - Average occurrences per word: {avg_occurrences:.1f}")

            if avg_occurrences >= verses_per_word_needed:
                print(f"  - FEASIBLE: Average word appears enough times")
            else:
                print(f"  - CHALLENGE: May need to include more frequency ranges")

    # Alternative strategies
    print(f"\nAlternative strategies:")
    print(f"  - Include 1x occurrences: +{only_once:,} words (may include proper nouns)")
    print(f"  - Include 501-2000x: +{bucket_counts.get('501-1000x', 0) + bucket_counts.get('1001-2000x', 0):,} words")
    print(f"  - Multiple verses per common word: Increases entry count significantly")

def main():
    """Main analysis function"""
    print("="*70)
    print("GOODBOOK.DB COMPREHENSIVE STATISTICAL ANALYSIS")
    print("="*70)
    print(f"Database: {DB_PATH}")

    try:
        # Connect to database
        conn = connect_db()
        print("[OK] Database connection successful")

        # Run all analyses
        word_freq, verse_count, total_words = analysis_1_basic_extraction(conn)
        bucket_counts = analysis_2_frequency_distribution(word_freq)
        length_dist = analysis_3_length_distribution(word_freq)
        top_words = analysis_4_common_words(word_freq)
        analysis_5_verse_context_sampling(conn, word_freq)
        analysis_6_reference_extraction(conn, word_freq)
        analysis_7_duplicate_words(conn)
        analysis_8_capacity_projection(word_freq, bucket_counts, length_dist)

        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)
        print("\nNext steps:")
        print("1. Review the findings above")
        print("2. Determine optimal frequency and length ranges")
        print("3. Design extraction strategy in extraction_design.md")
        print("4. Implement extract_crossword_entries.py")

        conn.close()

    except Exception as e:
        print(f"\n[ERROR] Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
