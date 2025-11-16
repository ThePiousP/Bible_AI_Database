#!/usr/bin/env python3
"""
Clue Quality Assessment
Analyzes clue coverage, distribution, uniqueness, and quality from Complete_bible_list.txt
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime


# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
CLUES_FILE = PROJECT_ROOT / "dev" / "Complete_bible_list.txt"
OUTPUT_DIR = PROJECT_ROOT / "output" / "Analytics"
OUTPUT_FILE = OUTPUT_DIR / "clue_quality.json"


def parse_clue_file():
    """Parse the Complete_bible_list.txt file and extract words and clues"""
    if not CLUES_FILE.exists():
        print(f"   Error: Clue file not found at {CLUES_FILE}")
        return []

    entries = []

    with open(CLUES_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.rstrip('\n\r')
            if not line.strip():
                continue

            # Split by tabs
            parts = line.split('\t')

            if len(parts) < 1:
                continue

            word = parts[0].strip()
            clues = [part.strip() for part in parts[1:] if part.strip()]

            entries.append({
                'line_number': line_num,
                'word': word,
                'clues': clues,
                'clue_count': len(clues)
            })

    return entries


def analyze_clue_coverage(entries):
    """Analyze how many clues each word has"""
    total_words = len(entries)
    total_clues = sum(entry['clue_count'] for entry in entries)

    # Distribution
    words_with_0_clues = sum(1 for entry in entries if entry['clue_count'] == 0)
    words_with_1_clue = sum(1 for entry in entries if entry['clue_count'] == 1)
    words_with_2_clues = sum(1 for entry in entries if entry['clue_count'] == 2)
    words_with_3_clues = sum(1 for entry in entries if entry['clue_count'] == 3)
    words_with_4plus_clues = sum(1 for entry in entries if entry['clue_count'] >= 4)

    # Statistics
    clue_counts = [entry['clue_count'] for entry in entries]
    avg_clues = sum(clue_counts) / len(clue_counts) if clue_counts else 0
    min_clues = min(clue_counts) if clue_counts else 0
    max_clues = max(clue_counts) if clue_counts else 0

    # Coverage percentage
    coverage_percentage = ((total_words - words_with_0_clues) / total_words * 100) if total_words > 0 else 0

    return {
        'total_words': total_words,
        'total_clues': total_clues,
        'average_clues_per_word': round(avg_clues, 2),
        'min_clues': min_clues,
        'max_clues': max_clues,
        'coverage_percentage': round(coverage_percentage, 2),
        'distribution': {
            'words_with_0_clues': words_with_0_clues,
            'words_with_1_clue': words_with_1_clue,
            'words_with_2_clues': words_with_2_clues,
            'words_with_3_clues': words_with_3_clues,
            'words_with_4plus_clues': words_with_4plus_clues
        }
    }


def analyze_clue_lengths(entries):
    """Analyze the length distribution of clues"""
    clue_lengths = []
    clue_word_counts = []

    for entry in entries:
        for clue in entry['clues']:
            # Character length
            clue_lengths.append(len(clue))

            # Word count
            words = clue.split()
            clue_word_counts.append(len(words))

    if not clue_lengths:
        return {}

    avg_char_length = sum(clue_lengths) / len(clue_lengths)
    avg_word_count = sum(clue_word_counts) / len(clue_word_counts)

    # Distribution by character length ranges
    length_ranges = {
        '0-20': sum(1 for l in clue_lengths if 0 <= l <= 20),
        '21-40': sum(1 for l in clue_lengths if 21 <= l <= 40),
        '41-60': sum(1 for l in clue_lengths if 41 <= l <= 60),
        '61-80': sum(1 for l in clue_lengths if 61 <= l <= 80),
        '81-100': sum(1 for l in clue_lengths if 81 <= l <= 100),
        '100+': sum(1 for l in clue_lengths if l > 100)
    }

    return {
        'average_character_length': round(avg_char_length, 1),
        'average_word_count': round(avg_word_count, 1),
        'min_character_length': min(clue_lengths),
        'max_character_length': max(clue_lengths),
        'length_distribution': length_ranges
    }


def detect_duplicate_clues(entries):
    """Detect duplicate clues across different words"""
    clue_to_words = defaultdict(list)

    for entry in entries:
        for clue in entry['clues']:
            # Normalize clue for comparison
            normalized_clue = clue.strip().lower()
            clue_to_words[normalized_clue].append(entry['word'])

    # Find duplicates
    duplicates = {clue: words for clue, words in clue_to_words.items() if len(words) > 1}

    # Sort by number of words using this clue
    sorted_duplicates = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)

    return {
        'total_unique_clues': len(clue_to_words),
        'duplicate_clues_count': len(duplicates),
        'duplicate_percentage': round(len(duplicates) / len(clue_to_words) * 100, 2) if clue_to_words else 0,
        'top_duplicates': [
            {'clue': clue, 'word_count': len(words), 'words': words[:10]}
            for clue, words in sorted_duplicates[:20]
        ]
    }


def categorize_clue_types(entries):
    """Attempt to categorize clues by type"""
    categories = {
        'definition': 0,
        'biblical_reference': 0,
        'relationship': 0,
        'location': 0,
        'occupation': 0,
        'description': 0,
        'other': 0
    }

    # Patterns for classification
    biblical_ref_pattern = re.compile(r'\b(Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Psalms|Proverbs|Ecclesiastes|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|Corinthians|Galatians|Ephesians|Philippians|Colossians|Thessalonians|Timothy|Titus|Philemon|Hebrews|James|Peter|Jude|Revelation)\s+\d+:\d+', re.IGNORECASE)
    relationship_pattern = re.compile(r'\b(son of|daughter of|father of|mother of|wife of|husband of|brother of|sister of|descendant)\b', re.IGNORECASE)
    location_pattern = re.compile(r'\b(city|town|river|mountain|place|region|land|country|territory)\b', re.IGNORECASE)
    occupation_pattern = re.compile(r'\b(king|priest|prophet|judge|apostle|scribe|pharisee|disciple|servant|official|eunuch)\b', re.IGNORECASE)

    for entry in entries:
        for clue in entry['clues']:
            if biblical_ref_pattern.search(clue):
                categories['biblical_reference'] += 1
            elif relationship_pattern.search(clue):
                categories['relationship'] += 1
            elif location_pattern.search(clue):
                categories['location'] += 1
            elif occupation_pattern.search(clue):
                categories['occupation'] += 1
            elif len(clue.split()) <= 5:
                categories['definition'] += 1
            else:
                categories['description'] += 1

    total = sum(categories.values())
    percentages = {k: round(v / total * 100, 2) if total > 0 else 0 for k, v in categories.items()}

    return {
        'counts': categories,
        'percentages': percentages
    }


def find_words_needing_clues(entries):
    """Identify words that need more clues"""
    needs_clues = []

    for entry in entries:
        if entry['clue_count'] == 0:
            needs_clues.append({
                'word': entry['word'],
                'current_clues': 0,
                'priority': 'high'
            })
        elif entry['clue_count'] == 1:
            needs_clues.append({
                'word': entry['word'],
                'current_clues': 1,
                'priority': 'medium'
            })

    return {
        'high_priority': [w for w in needs_clues if w['priority'] == 'high'],
        'medium_priority': [w for w in needs_clues if w['priority'] == 'medium'],
        'total_needing_improvement': len(needs_clues)
    }


def main():
    """Main analysis function"""
    print("Starting Clue Quality Assessment...")
    print(f"Output will be saved to: {OUTPUT_FILE}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Parse clue file
    print(f"\n1. Parsing clue file: {CLUES_FILE}...")
    entries = parse_clue_file()
    print(f"   -> Found {len(entries):,} word entries")

    if not entries:
        print("\n[WARNING] Error: No entries found in clue file")
        return None

    # Perform analyses
    print("\n2. Analyzing clue coverage...")
    coverage = analyze_clue_coverage(entries)
    print(f"   -> Total clues: {coverage['total_clues']:,}")
    print(f"   -> Average clues per word: {coverage['average_clues_per_word']}")
    print(f"   -> Coverage: {coverage['coverage_percentage']}%")

    print("\n3. Analyzing clue lengths...")
    lengths = analyze_clue_lengths(entries)
    print(f"   -> Average length: {lengths.get('average_character_length', 0)} characters")
    print(f"   -> Average words: {lengths.get('average_word_count', 0)} words")

    print("\n4. Detecting duplicate clues...")
    duplicates = detect_duplicate_clues(entries)
    print(f"   -> Unique clues: {duplicates['total_unique_clues']:,}")
    print(f"   -> Duplicates: {duplicates['duplicate_clues_count']:,} ({duplicates['duplicate_percentage']}%)")

    print("\n5. Categorizing clue types...")
    categories = categorize_clue_types(entries)
    print(f"   -> Most common type: {max(categories['counts'].items(), key=lambda x: x[1])[0]}")

    print("\n6. Identifying words needing clues...")
    needs_clues = find_words_needing_clues(entries)
    print(f"   -> High priority (0 clues): {len(needs_clues['high_priority'])}")
    print(f"   -> Medium priority (1 clue): {len(needs_clues['medium_priority'])}")

    # Compile results
    results = {
        'metadata': {
            'analysis_date': datetime.now().isoformat(),
            'clue_file': str(CLUES_FILE)
        },
        'coverage': coverage,
        'clue_lengths': lengths,
        'duplicates': duplicates,
        'clue_types': categories,
        'words_needing_clues': {
            'summary': {
                'high_priority_count': len(needs_clues['high_priority']),
                'medium_priority_count': len(needs_clues['medium_priority']),
                'total_needing_improvement': needs_clues['total_needing_improvement']
            },
            'high_priority_sample': needs_clues['high_priority'][:50],
            'medium_priority_sample': needs_clues['medium_priority'][:50]
        }
    }

    # Save to JSON
    print(f"\n7. Saving results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n[DONE] Clue Quality Assessment Complete!")
    print(f"  Output: {OUTPUT_FILE}")

    return results


if __name__ == "__main__":
    main()
