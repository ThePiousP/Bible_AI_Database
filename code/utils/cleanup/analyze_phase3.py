#!/usr/bin/env python3
"""
Phase 3 Statistical Analysis
Analyzes protected biblical terms to find optimal frequency range and verse targets
"""

import sqlite3
import json
import glob
import re
from collections import Counter, defaultdict

# Database
DB_PATH = r"D:\Project_PP\projects\bible\data\GoodBook.db"

# Curated entries
CURATED_ENTRIES_PATH = r"D:\Project_PP\projects\bible\data\*.json"

# Output
OUTPUT_PATH = r"D:\Project_PP\projects\bible\phase3_targets.txt"

# Protected biblical terms (base set)
PROTECTED_BIBLICAL_TERMS = {
    'DAVID', 'SAUL', 'MOSES', 'ABRAHAM', 'ISAAC', 'JACOB', 'JOSEPH',
    'JOSHUA', 'SAMUEL', 'SOLOMON', 'ELIJAH', 'ELISHA', 'DANIEL',
    'JESUS', 'CHRIST', 'PAUL', 'PETER', 'JOHN', 'JAMES',
    'JERUSALEM', 'ISRAEL', 'JUDAH', 'EGYPT', 'BABYLON', 'BETHLEHEM',
    'NAZARETH', 'GALILEE', 'JORDAN', 'SINAI',
    'GOD', 'LORD', 'SPIRIT', 'HOLY', 'HEAVEN', 'GLORY', 'GRACE',
    'RIGHTEOUS', 'COVENANT', 'FAITH', 'BLESSED', 'SANCTIFIED',
    'ALTAR', 'TEMPLE', 'TABERNACLE', 'ARK', 'FIRE', 'BLOOD',
    'COMMANDED', 'BLESSED', 'PROPHESY', 'SACRIFICE', 'WORSHIP',
    'PROMISED', 'ANOINTED',
    'EARTH', 'HEAVEN', 'SEA', 'MOUNTAIN', 'WILDERNESS'
}

WORD_PATTERN = r'\b[A-Za-z]{3,15}\b'


def load_curated_words(json_pattern):
    """Load words from curated JSON entries"""
    curated_words = set()
    json_files = glob.glob(json_pattern)

    print(f"Loading curated words from {len(json_files)} files...")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                if isinstance(data, dict):
                    for category_name, category_data in data.items():
                        if isinstance(category_data, dict):
                            for word, details in category_data.items():
                                if ' ' in word:
                                    parts = word.split()
                                    for part in parts:
                                        clean_part = part.strip().upper()
                                        if len(clean_part) >= 3:
                                            curated_words.add(clean_part)
                                else:
                                    clean_word = word.strip().upper()
                                    if len(clean_word) >= 3:
                                        curated_words.add(clean_word)
        except Exception as e:
            print(f"  Warning: Could not load {json_file}: {e}")

    return curated_words


def get_word_frequency(conn, word):
    """Get frequency of a word in the verses table"""
    cursor = conn.cursor()

    query = """
        SELECT COUNT(*) as freq
        FROM verses
        WHERE UPPER(text) LIKE ?
        AND text IS NOT NULL
    """

    cursor.execute(query, (f'%{word}%',))
    result = cursor.fetchone()

    if not result:
        return 0

    # Now verify it's a complete word match
    cursor.execute("""
        SELECT text FROM verses
        WHERE UPPER(text) LIKE ?
        AND text IS NOT NULL
    """, (f'%{word}%',))

    pattern = r'\b' + re.escape(word) + r'\b'
    actual_count = 0

    for (text,) in cursor:
        if re.search(pattern, text, re.IGNORECASE):
            actual_count += 1

    return actual_count


def analyze_protected_words(conn, protected_words):
    """Analyze frequency distribution of all protected words"""
    print("\nAnalyzing protected word frequencies...")
    print(f"Total protected words to analyze: {len(protected_words):,}")

    word_frequencies = {}
    processed = 0

    for word in sorted(protected_words):
        processed += 1
        if processed % 100 == 0:
            print(f"  Progress: {processed}/{len(protected_words)} words...")

        freq = get_word_frequency(conn, word)
        word_frequencies[word] = freq

    return word_frequencies


def generate_statistics(word_frequencies):
    """Generate comprehensive statistics"""
    print("\n" + "="*70)
    print("PHASE 3 STATISTICAL ANALYSIS")
    print("="*70)

    # Overall stats
    total_words = len(word_frequencies)
    words_with_occurrences = sum(1 for f in word_frequencies.values() if f > 0)

    print(f"\nOVERALL STATISTICS")
    print(f"  Total protected words: {total_words:,}")
    print(f"  Words with occurrences: {words_with_occurrences:,}")
    print(f"  Words with no occurrences: {total_words - words_with_occurrences:,}")

    # Frequency distribution
    freq_buckets = defaultdict(list)

    for word, freq in word_frequencies.items():
        if freq == 0:
            freq_buckets['0'].append(word)
        elif freq == 1:
            freq_buckets['1'].append(word)
        elif 2 <= freq <= 5:
            freq_buckets['2-5'].append(word)
        elif 6 <= freq <= 10:
            freq_buckets['6-10'].append(word)
        elif 11 <= freq <= 25:
            freq_buckets['11-25'].append(word)
        elif 26 <= freq <= 50:
            freq_buckets['26-50'].append(word)
        elif 51 <= freq <= 100:
            freq_buckets['51-100'].append(word)
        elif 101 <= freq <= 250:
            freq_buckets['101-250'].append(word)
        elif 251 <= freq <= 500:
            freq_buckets['251-500'].append(word)
        elif 501 <= freq <= 1000:
            freq_buckets['501-1000'].append(word)
        else:
            freq_buckets['1000+'].append(word)

    print(f"\nFREQUENCY DISTRIBUTION")
    print(f"  {'Range':<15} {'Count':<10} {'Words'}")
    print(f"  {'-'*15} {'-'*10} {'-'*40}")

    for bucket in ['0', '1', '2-5', '6-10', '11-25', '26-50', '51-100',
                   '101-250', '251-500', '501-1000', '1000+']:
        words = freq_buckets[bucket]
        count = len(words)
        examples = ', '.join(sorted(words)[:5])
        if len(words) > 5:
            examples += "..."
        print(f"  {bucket:<15} {count:<10} {examples}")

    # Analyze different frequency ranges for Phase 3
    print(f"\nPHASE 3 RANGE ANALYSIS")
    print(f"  Testing different frequency ranges for optimal results:")
    print(f"  {'Range':<20} {'Words Available':<20} {'Potential Entries'}")
    print(f"  {'-'*20} {'-'*20} {'-'*20}")

    ranges_to_test = [
        (50, 500),
        (50, 1000),
        (75, 500),
        (100, 500),
        (100, 1000),
        (25, 500),
        (25, 250),
    ]

    for min_freq, max_freq in ranges_to_test:
        words_in_range = [w for w, f in word_frequencies.items()
                         if min_freq <= f <= max_freq]

        # Estimate potential entries (assuming 3-5 verses per word)
        min_entries = len(words_in_range) * 3
        max_entries = len(words_in_range) * 5

        print(f"  {min_freq}-{max_freq:<15} {len(words_in_range):<20} {min_entries:,}-{max_entries:,}")

    # Top words by frequency
    print(f"\nTOP 30 PROTECTED WORDS BY FREQUENCY")
    sorted_words = sorted(word_frequencies.items(), key=lambda x: -x[1])
    for i, (word, freq) in enumerate(sorted_words[:30], 1):
        print(f"  {i:2}. {word:<20} {freq:>6} occurrences")

    return freq_buckets


def recommend_optimal_range(word_frequencies):
    """Recommend optimal frequency range and verse targets"""
    print("\n" + "="*70)
    print("RECOMMENDATIONS FOR PHASE 3")
    print("="*70)

    # Analyze different ranges
    ranges_analysis = {}

    for min_freq in [25, 50, 75, 100]:
        for max_freq in [250, 500, 750, 1000]:
            if max_freq <= min_freq:
                continue

            words_in_range = [
                (w, f) for w, f in word_frequencies.items()
                if min_freq <= f <= max_freq
            ]

            if not words_in_range:
                continue

            # Calculate metrics
            word_count = len(words_in_range)
            avg_freq = sum(f for w, f in words_in_range) / word_count if word_count > 0 else 0

            # Estimate verses per word (conservative)
            # Higher frequency = more verses available
            if avg_freq < 100:
                verses_per_word = 2
            elif avg_freq < 200:
                verses_per_word = 3
            elif avg_freq < 400:
                verses_per_word = 4
            else:
                verses_per_word = 5

            potential_entries = word_count * verses_per_word

            ranges_analysis[(min_freq, max_freq)] = {
                'word_count': word_count,
                'avg_freq': avg_freq,
                'verses_per_word': verses_per_word,
                'potential_entries': potential_entries
            }

    # Find best range (target ~5000-10000 entries)
    best_range = None
    best_score = 0
    target_entries = 7500  # Sweet spot

    for (min_freq, max_freq), metrics in ranges_analysis.items():
        # Score based on closeness to target
        entries = metrics['potential_entries']

        if entries < 1000:  # Too few
            score = 0
        elif entries > 15000:  # Too many
            score = entries / 100
        else:
            # Prefer ranges close to target
            score = 10000 - abs(entries - target_entries)

        if score > best_score:
            best_score = score
            best_range = (min_freq, max_freq, metrics)

    if best_range:
        min_freq, max_freq, metrics = best_range

        print(f"\nRECOMMENDED CONFIGURATION:")
        print(f"  Frequency range: {min_freq}-{max_freq}")
        print(f"  Words available: {metrics['word_count']:,}")
        print(f"  Average frequency: {metrics['avg_freq']:.1f}")
        print(f"  Verses per word: {metrics['verses_per_word']}")
        print(f"  Estimated entries: {metrics['potential_entries']:,}")
        print(f"  Target for Phase 3: {metrics['potential_entries']:,}")

        return min_freq, max_freq, metrics['verses_per_word'], metrics['potential_entries']

    return 50, 500, 3, 5000


def write_targets_file(output_path, min_freq, max_freq, verses_per_word, target_entries, word_frequencies):
    """Write phase3_targets.txt with recommendations"""
    print(f"\nWriting targets to {output_path}...")

    # Get words in recommended range
    words_in_range = sorted(
        [(w, f) for w, f in word_frequencies.items() if min_freq <= f <= max_freq],
        key=lambda x: -x[1]
    )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("PHASE 3 OPTIMIZATION TARGETS\n")
        f.write("="*70 + "\n\n")

        f.write("RECOMMENDED CONFIGURATION\n")
        f.write("-" * 70 + "\n")
        f.write(f"MIN_FREQUENCY:        {min_freq}\n")
        f.write(f"MAX_FREQUENCY:        {max_freq}\n")
        f.write(f"VERSES_PER_WORD:      {verses_per_word}\n")
        f.write(f"PHASE_3_TARGET:       {target_entries:,}\n")
        f.write(f"WORDS_AVAILABLE:      {len(words_in_range):,}\n")
        f.write("\n")

        f.write("WORDS IN RECOMMENDED RANGE (sorted by frequency)\n")
        f.write("-" * 70 + "\n")
        f.write(f"{'Word':<20} {'Frequency':<15} {'Est. Verses'}\n")
        f.write("-" * 70 + "\n")

        for word, freq in words_in_range:
            f.write(f"{word:<20} {freq:<15} {verses_per_word}\n")

        f.write("\n")
        f.write("CODE CHANGES NEEDED\n")
        f.write("-" * 70 + "\n")
        f.write("In extract_crossword_entries.py, update extract_phase_3():\n\n")
        f.write(f"  Line ~598: if {min_freq} <= f <= {max_freq}  # Change from 100 <= f <= 1000\n")
        f.write(f"  Line ~615: verses_per_word = {verses_per_word}  # Change from 3\n")
        f.write(f"  Line ~49:  PHASE_3_TARGET = {target_entries}  # Change from 5000\n")
        f.write(f"  Line ~593: print statement: 'freq {min_freq}-{max_freq}'\n")
        f.write("\n")

    print(f"  Targets file written successfully")


def main():
    """Main analysis workflow"""
    # Connect to database
    print("Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    print("  Connected")

    # Load protected words
    print("\nLoading protected words...")
    curated_words = load_curated_words(CURATED_ENTRIES_PATH)
    protected_words = PROTECTED_BIBLICAL_TERMS | curated_words
    print(f"  Total protected terms: {len(protected_words):,}")

    # Analyze frequencies
    word_frequencies = analyze_protected_words(conn, protected_words)

    # Generate statistics
    freq_buckets = generate_statistics(word_frequencies)

    # Recommend optimal range
    min_freq, max_freq, verses_per_word, target_entries = recommend_optimal_range(word_frequencies)

    # Write targets file
    write_targets_file(OUTPUT_PATH, min_freq, max_freq, verses_per_word,
                      target_entries, word_frequencies)

    # Close database
    conn.close()

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"Targets file: {OUTPUT_PATH}")
    print("="*70)


if __name__ == "__main__":
    main()
