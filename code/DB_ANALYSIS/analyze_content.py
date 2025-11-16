#!/usr/bin/env python3
"""
Content Distribution Analysis
Analyzes word length, letter frequency, bigrams, and character patterns
"""

import sqlite3
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime


# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
GOODBOOK_DB = PROJECT_ROOT / "data" / "GoodBook.db"
CONCORDANCE_DB = PROJECT_ROOT / "Folders" / "REFACTOR_BACKUPS" / "backup_2025-10-29_18-08-33" / "data" / "concordance.db"
CLUES_FILE = PROJECT_ROOT / "dev" / "Complete_bible_list.txt"
OUTPUT_DIR = PROJECT_ROOT / "output" / "Analytics"
OUTPUT_FILE = OUTPUT_DIR / "content_distribution.json"


def get_all_words():
    """Extract all unique words from databases and clue file"""
    words = set()

    # Get words from GoodBook.db lexical_words
    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT word FROM lexical_words WHERE word IS NOT NULL")
        for row in cursor.fetchall():
            if row[0]:
                words.add(row[0].strip())
        conn.close()

    # Get words from concordance.db tokens
    if CONCORDANCE_DB.exists():
        conn = sqlite3.connect(CONCORDANCE_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT text FROM tokens WHERE text IS NOT NULL AND TRIM(text) != ''")
        for row in cursor.fetchall():
            if row[0]:
                words.add(row[0].strip())
        conn.close()

    # Get words from clue file
    if CLUES_FILE.exists():
        with open(CLUES_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if parts:
                    word = parts[0].strip()
                    if word:
                        words.add(word)

    return list(words)


def analyze_word_lengths(words):
    """Analyze distribution of word lengths"""
    length_counts = Counter()

    for word in words:
        # Remove non-letter characters for length calculation
        clean_word = re.sub(r'[^a-zA-Z]', '', word)
        if clean_word:
            length_counts[len(clean_word)] += 1

    # Calculate statistics
    all_lengths = []
    for length, count in length_counts.items():
        all_lengths.extend([length] * count)

    avg_length = sum(all_lengths) / len(all_lengths) if all_lengths else 0

    return {
        'distribution': dict(sorted(length_counts.items())),
        'average_length': round(avg_length, 2),
        'min_length': min(length_counts.keys()) if length_counts else 0,
        'max_length': max(length_counts.keys()) if length_counts else 0,
        'total_words': len(words)
    }


def analyze_letter_frequency(words):
    """Analyze letter frequency across all words"""
    letter_counts = Counter()
    total_letters = 0

    for word in words:
        # Only count alphabetic characters
        clean_word = re.sub(r'[^a-zA-Z]', '', word.upper())
        for letter in clean_word:
            letter_counts[letter] += 1
            total_letters += 1

    # Calculate percentages
    letter_freq = {}
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        count = letter_counts.get(letter, 0)
        percentage = (count / total_letters * 100) if total_letters > 0 else 0
        letter_freq[letter] = {
            'count': count,
            'percentage': round(percentage, 2)
        }

    return {
        'frequencies': letter_freq,
        'total_letters': total_letters,
        'most_common': letter_counts.most_common(5),
        'least_common': letter_counts.most_common()[-5:] if len(letter_counts) >= 5 else []
    }


def analyze_vowel_consonant_ratio(words):
    """Calculate vowel to consonant ratios"""
    vowels = set('AEIOUaeiou')
    vowel_count = 0
    consonant_count = 0

    for word in words:
        for char in word:
            if char.isalpha():
                if char in vowels:
                    vowel_count += 1
                else:
                    consonant_count += 1

    total = vowel_count + consonant_count
    vowel_ratio = (vowel_count / total * 100) if total > 0 else 0
    consonant_ratio = (consonant_count / total * 100) if total > 0 else 0

    return {
        'vowels': vowel_count,
        'consonants': consonant_count,
        'total_letters': total,
        'vowel_percentage': round(vowel_ratio, 2),
        'consonant_percentage': round(consonant_ratio, 2)
    }


def analyze_bigrams(words):
    """Analyze most common letter pairs (bigrams)"""
    bigram_counts = Counter()

    for word in words:
        clean_word = re.sub(r'[^a-zA-Z]', '', word.upper())
        for i in range(len(clean_word) - 1):
            bigram = clean_word[i:i+2]
            bigram_counts[bigram] += 1

    return {
        'total_bigrams': sum(bigram_counts.values()),
        'unique_bigrams': len(bigram_counts),
        'most_common': bigram_counts.most_common(20),
        'least_common': bigram_counts.most_common()[-20:] if len(bigram_counts) >= 20 else []
    }


def analyze_rare_combinations(words):
    """Identify rare letter combinations"""
    # Trigrams
    trigram_counts = Counter()

    for word in words:
        clean_word = re.sub(r'[^a-zA-Z]', '', word.upper())
        for i in range(len(clean_word) - 2):
            trigram = clean_word[i:i+3]
            trigram_counts[trigram] += 1

    # Find rare trigrams (appearing only once or twice)
    rare_trigrams = [(trigram, count) for trigram, count in trigram_counts.items() if count <= 2]

    return {
        'total_trigrams': sum(trigram_counts.values()),
        'unique_trigrams': len(trigram_counts),
        'rare_trigrams_count': len(rare_trigrams),
        'rare_examples': sorted(rare_trigrams[:50], key=lambda x: x[0])
    }


def main():
    """Main analysis function"""
    print("Starting Content Distribution Analysis...")
    print(f"Output will be saved to: {OUTPUT_FILE}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get all words from various sources
    print("\n1. Extracting words from databases and files...")
    words = get_all_words()
    print(f"   -> Found {len(words):,} unique words")

    # Perform analyses
    print("\n2. Analyzing word lengths...")
    word_lengths = analyze_word_lengths(words)
    print(f"   -> Average word length: {word_lengths['average_length']} letters")

    print("\n3. Analyzing letter frequency...")
    letter_freq = analyze_letter_frequency(words)
    print(f"   -> Total letters analyzed: {letter_freq['total_letters']:,}")
    print(f"   -> Most common letter: {letter_freq['most_common'][0][0]} ({letter_freq['most_common'][0][1]:,} occurrences)")

    print("\n4. Analyzing vowel/consonant ratios...")
    vc_ratio = analyze_vowel_consonant_ratio(words)
    print(f"   -> Vowels: {vc_ratio['vowel_percentage']}%")
    print(f"   -> Consonants: {vc_ratio['consonant_percentage']}%")

    print("\n5. Analyzing bigrams (letter pairs)...")
    bigrams = analyze_bigrams(words)
    print(f"   -> Found {bigrams['unique_bigrams']:,} unique bigrams")
    print(f"   -> Most common: {bigrams['most_common'][0][0]} ({bigrams['most_common'][0][1]:,} occurrences)")

    print("\n6. Identifying rare letter combinations...")
    rare = analyze_rare_combinations(words)
    print(f"   -> Found {rare['rare_trigrams_count']:,} rare trigrams")

    # Compile results
    results = {
        'metadata': {
            'analysis_date': datetime.now().isoformat(),
            'total_unique_words': len(words),
            'sources': {
                'goodbook_db': str(GOODBOOK_DB),
                'concordance_db': str(CONCORDANCE_DB),
                'clues_file': str(CLUES_FILE)
            }
        },
        'word_length_distribution': word_lengths,
        'letter_frequency': letter_freq,
        'vowel_consonant_ratio': vc_ratio,
        'bigrams': bigrams,
        'rare_combinations': rare
    }

    # Save to JSON
    print(f"\n7. Saving results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n[DONE] Content Distribution Analysis Complete!")
    print(f"  Output: {OUTPUT_FILE}")

    return results


if __name__ == "__main__":
    main()
