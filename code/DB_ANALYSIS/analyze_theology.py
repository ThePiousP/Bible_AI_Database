#!/usr/bin/env python3
"""
Theological Coverage Analysis
Analyzes distribution by biblical books, OT/NT balance, Strong's coverage, entity types
"""

import sqlite3
import json
import os
import glob
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime


# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
GOODBOOK_DB = PROJECT_ROOT / "data" / "GoodBook.db"
CONCORDANCE_DB = PROJECT_ROOT / "Folders" / "REFACTOR_BACKUPS" / "backup_2025-10-29_18-08-33" / "data" / "concordance.db"
ENTITY_DIR = PROJECT_ROOT / "bible_entities"
OUTPUT_DIR = PROJECT_ROOT / "output" / "Analytics"
OUTPUT_FILE = OUTPUT_DIR / "theology_coverage.json"

# Old Testament books (39 books)
OT_BOOKS = {
    'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
    'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings',
    '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Esther',
    'Job', 'Psalms', 'Proverbs', 'Ecclesiastes', 'Song of Solomon',
    'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel',
    'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah',
    'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi'
}

# New Testament books (27 books)
NT_BOOKS = {
    'Matthew', 'Mark', 'Luke', 'John', 'Acts',
    'Romans', '1 Corinthians', '2 Corinthians', 'Galatians',
    'Ephesians', 'Philippians', 'Colossians',
    '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy',
    'Titus', 'Philemon', 'Hebrews', 'James',
    '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation'
}


def get_book_distribution():
    """Analyze word/verse distribution across biblical books"""
    book_stats = defaultdict(lambda: {'verses': 0, 'words': 0, 'chapters': 0})

    # From GoodBook.db
    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        # Get verse counts by book
        cursor.execute("""
            SELECT b.book_name, COUNT(DISTINCT v.id) as verse_count, COUNT(DISTINCT c.id) as chapter_count
            FROM books b
            LEFT JOIN chapters c ON c.book_id = b.id
            LEFT JOIN verses v ON v.chapter_id = c.id
            GROUP BY b.book_name
        """)

        for book_name, verse_count, chapter_count in cursor.fetchall():
            book_stats[book_name]['verses'] += verse_count
            book_stats[book_name]['chapters'] += chapter_count

        # Get word counts from lexical_words via verse_words
        cursor.execute("""
            SELECT b.book_name, COUNT(vw.id) as word_count
            FROM books b
            LEFT JOIN chapters c ON c.book_id = b.id
            LEFT JOIN verses v ON v.chapter_id = c.id
            LEFT JOIN verse_words vw ON vw.verse_id = v.id
            GROUP BY b.book_name
        """)

        for book_name, word_count in cursor.fetchall():
            book_stats[book_name]['words'] += word_count

        conn.close()

    # From concordance.db
    if CONCORDANCE_DB.exists():
        conn = sqlite3.connect(CONCORDANCE_DB)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT b.book_name, COUNT(DISTINCT v.id) as verse_count, COUNT(t.id) as token_count
            FROM books b
            LEFT JOIN verses v ON v.book_id = b.id
            LEFT JOIN tokens t ON t.verse_id = v.id
            GROUP BY b.book_name
        """)

        for book_name, verse_count, token_count in cursor.fetchall():
            # Only update if we don't have data from GoodBook
            if book_stats[book_name]['verses'] == 0:
                book_stats[book_name]['verses'] = verse_count
            if book_stats[book_name]['words'] == 0:
                book_stats[book_name]['words'] = token_count

        conn.close()

    return dict(book_stats)


def analyze_testament_balance(book_stats):
    """Analyze Old Testament vs New Testament balance"""
    ot_stats = {'books': 0, 'verses': 0, 'words': 0, 'chapters': 0}
    nt_stats = {'books': 0, 'verses': 0, 'words': 0, 'chapters': 0}
    unknown_stats = {'books': 0, 'verses': 0, 'words': 0, 'chapters': 0}

    for book, stats in book_stats.items():
        if book in OT_BOOKS:
            ot_stats['books'] += 1
            ot_stats['verses'] += stats['verses']
            ot_stats['words'] += stats['words']
            ot_stats['chapters'] += stats['chapters']
        elif book in NT_BOOKS:
            nt_stats['books'] += 1
            nt_stats['verses'] += stats['verses']
            nt_stats['words'] += stats['words']
            nt_stats['chapters'] += stats['chapters']
        else:
            unknown_stats['books'] += 1
            unknown_stats['verses'] += stats['verses']
            unknown_stats['words'] += stats['words']
            unknown_stats['chapters'] += stats['chapters']

    total_verses = ot_stats['verses'] + nt_stats['verses']
    total_words = ot_stats['words'] + nt_stats['words']

    return {
        'old_testament': {
            **ot_stats,
            'verse_percentage': round(ot_stats['verses'] / total_verses * 100, 2) if total_verses > 0 else 0,
            'word_percentage': round(ot_stats['words'] / total_words * 100, 2) if total_words > 0 else 0
        },
        'new_testament': {
            **nt_stats,
            'verse_percentage': round(nt_stats['verses'] / total_verses * 100, 2) if total_verses > 0 else 0,
            'word_percentage': round(nt_stats['words'] / total_words * 100, 2) if total_words > 0 else 0
        },
        'unknown': unknown_stats if unknown_stats['books'] > 0 else None
    }


def analyze_strongs_coverage():
    """Analyze Strong's number coverage"""
    strongs_numbers = set()
    hebrew_strongs = set()
    greek_strongs = set()

    # From GoodBook.db
    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT strongs_number, language FROM lexical_words WHERE strongs_number IS NOT NULL")
        for strongs, lang in cursor.fetchall():
            strongs_numbers.add(strongs)
            if lang == 'Hebrew':
                hebrew_strongs.add(strongs)
            elif lang == 'Greek':
                greek_strongs.add(strongs)

        conn.close()

    # From concordance.db
    if CONCORDANCE_DB.exists():
        conn = sqlite3.connect(CONCORDANCE_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT strong_norm FROM strongs_lexicon WHERE strong_norm IS NOT NULL")
        for (strongs,) in cursor.fetchall():
            strongs_numbers.add(strongs)
            if strongs.startswith('H'):
                hebrew_strongs.add(strongs)
            elif strongs.startswith('G'):
                greek_strongs.add(strongs)

        conn.close()

    # Analyze gaps in sequence
    hebrew_nums = sorted([int(s[1:]) for s in hebrew_strongs if s.startswith('H') and s[1:].isdigit()])
    greek_nums = sorted([int(s[1:]) for s in greek_strongs if s.startswith('G') and s[1:].isdigit()])

    hebrew_gaps = []
    if hebrew_nums:
        for i in range(hebrew_nums[0], hebrew_nums[-1] + 1):
            if i not in hebrew_nums:
                hebrew_gaps.append(f"H{i:04d}")

    greek_gaps = []
    if greek_nums:
        for i in range(greek_nums[0], greek_nums[-1] + 1):
            if i not in greek_nums:
                greek_gaps.append(f"G{i:04d}")

    # Known Strong's ranges: Hebrew 1-8674, Greek 1-5624
    expected_hebrew = 8674
    expected_greek = 5624

    return {
        'total_strongs_numbers': len(strongs_numbers),
        'hebrew': {
            'count': len(hebrew_strongs),
            'expected': expected_hebrew,
            'coverage_percentage': round(len(hebrew_strongs) / expected_hebrew * 100, 2),
            'gaps_count': len(hebrew_gaps),
            'sample_gaps': hebrew_gaps[:20]
        },
        'greek': {
            'count': len(greek_strongs),
            'expected': expected_greek,
            'coverage_percentage': round(len(greek_strongs) / expected_greek * 100, 2),
            'gaps_count': len(greek_gaps),
            'sample_gaps': greek_gaps[:20]
        }
    }


def analyze_entity_types():
    """Analyze entity type distribution from JSON files"""
    entity_stats = {}

    if ENTITY_DIR.exists():
        for json_file in ENTITY_DIR.glob("*.json"):
            entity_type = json_file.stem
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        count = len(data)
                    elif isinstance(data, dict):
                        count = len(data.keys())
                    else:
                        count = 0

                    entity_stats[entity_type] = {
                        'count': count,
                        'file': str(json_file.name)
                    }
            except Exception as e:
                print(f"   Warning: Could not read {json_file.name}: {e}")

    return entity_stats


def analyze_theological_concepts():
    """Analyze theological concept frequency in verse text"""
    concepts = {
        'grace': 0, 'mercy': 0, 'love': 0, 'faith': 0, 'hope': 0,
        'redemption': 0, 'salvation': 0, 'covenant': 0, 'righteousness': 0,
        'sin': 0, 'forgiveness': 0, 'sacrifice': 0, 'prayer': 0,
        'worship': 0, 'holy': 0, 'spirit': 0, 'law': 0, 'gospel': 0
    }

    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        for concept in concepts.keys():
            cursor.execute(f"SELECT COUNT(*) FROM verses WHERE LOWER(text) LIKE '%{concept.lower()}%'")
            count = cursor.fetchone()[0]
            concepts[concept] = count

        conn.close()

    # Sort by frequency
    sorted_concepts = sorted(concepts.items(), key=lambda x: x[1], reverse=True)

    return {
        'concepts': concepts,
        'most_frequent': sorted_concepts[:10],
        'least_frequent': sorted_concepts[-10:]
    }


def main():
    """Main analysis function"""
    print("Starting Theological Coverage Analysis...")
    print(f"Output will be saved to: {OUTPUT_FILE}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Perform analyses
    print("\n1. Analyzing book distribution...")
    book_stats = get_book_distribution()
    print(f"   -> Found {len(book_stats)} books")

    print("\n2. Analyzing Testament balance (OT vs NT)...")
    testament_balance = analyze_testament_balance(book_stats)
    print(f"   -> OT: {testament_balance['old_testament']['books']} books, {testament_balance['old_testament']['verses']:,} verses")
    print(f"   -> NT: {testament_balance['new_testament']['books']} books, {testament_balance['new_testament']['verses']:,} verses")

    print("\n3. Analyzing Strong's number coverage...")
    strongs_coverage = analyze_strongs_coverage()
    print(f"   -> Hebrew: {strongs_coverage['hebrew']['count']:,} / {strongs_coverage['hebrew']['expected']:,} ({strongs_coverage['hebrew']['coverage_percentage']}%)")
    print(f"   -> Greek: {strongs_coverage['greek']['count']:,} / {strongs_coverage['greek']['expected']:,} ({strongs_coverage['greek']['coverage_percentage']}%)")

    print("\n4. Analyzing entity types...")
    entity_types = analyze_entity_types()
    print(f"   -> Found {len(entity_types)} entity types")

    print("\n5. Analyzing theological concepts...")
    concepts = analyze_theological_concepts()
    print(f"   -> Most common concept: {concepts['most_frequent'][0][0]} ({concepts['most_frequent'][0][1]:,} occurrences)")

    # Compile results
    results = {
        'metadata': {
            'analysis_date': datetime.now().isoformat(),
            'databases_analyzed': {
                'goodbook_db': str(GOODBOOK_DB),
                'concordance_db': str(CONCORDANCE_DB)
            }
        },
        'book_distribution': book_stats,
        'testament_balance': testament_balance,
        'strongs_coverage': strongs_coverage,
        'entity_types': entity_types,
        'theological_concepts': concepts
    }

    # Save to JSON
    print(f"\n6. Saving results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n[DONE] Theological Coverage Analysis Complete!")
    print(f"  Output: {OUTPUT_FILE}")

    return results


if __name__ == "__main__":
    main()
