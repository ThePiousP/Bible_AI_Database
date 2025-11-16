#!/usr/bin/env python3
"""
Difficulty & Accessibility Profile Analysis
Analyzes word frequency, reading level, Greek/Hebrew terms, accessibility
"""

import sqlite3
import json
import re
from collections import Counter
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple


# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
GOODBOOK_DB = PROJECT_ROOT / "data" / "GoodBook.db"
CONCORDANCE_DB = PROJECT_ROOT / "Folders" / "REFACTOR_BACKUPS" / "backup_2025-10-29_18-08-33" / "data" / "concordance.db"
CLUES_FILE = PROJECT_ROOT / "dev" / "Complete_bible_list.txt"
OUTPUT_DIR = PROJECT_ROOT / "output" / "Analytics"
OUTPUT_FILE = OUTPUT_DIR / "difficulty_profile.json"

# Common English words (subset for frequency classification)
COMMON_WORDS = {
    'the', 'and', 'of', 'to', 'a', 'in', 'that', 'is', 'was', 'he', 'for', 'it', 'with', 'as', 'his', 'on',
    'be', 'at', 'by', 'i', 'this', 'had', 'not', 'are', 'but', 'from', 'or', 'have', 'an', 'they', 'which',
    'one', 'you', 'were', 'her', 'all', 'she', 'there', 'would', 'their', 'we', 'him', 'been', 'has', 'when',
    'who', 'will', 'more', 'if', 'no', 'out', 'so', 'said', 'what', 'up', 'its', 'about', 'than', 'into',
    'them', 'can', 'only', 'other', 'new', 'some', 'could', 'time', 'these', 'two', 'may', 'then', 'do',
    'first', 'any', 'my', 'now', 'such', 'like', 'our', 'over', 'man', 'me', 'even', 'most', 'made', 'after',
    'also', 'did', 'many', 'before', 'must', 'through', 'back', 'years', 'where', 'much', 'your', 'way', 'well',
    'down', 'should', 'because', 'each', 'just', 'those', 'people', 'mr', 'how', 'too', 'little', 'state',
    'good', 'very', 'make', 'world', 'still', 'own', 'see', 'men', 'work', 'long', 'get', 'here', 'between'
}


def get_word_frequencies():
    """Calculate word frequency from verse text"""
    word_freq = Counter()

    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT text FROM verses WHERE text IS NOT NULL")
        for (text,) in cursor.fetchall():
            # Extract words (letters only)
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            word_freq.update(words)

        conn.close()

    return word_freq


def classify_words_by_frequency(word_freq: Counter) -> Dict[str, Dict[str, Any]]:
    """Classify words into common, uncommon, and rare categories"""
    if not word_freq:
        return {
            'common': {'count': 0, 'percentage': 0.0, 'examples': []},
            'uncommon': {'count': 0, 'percentage': 0.0, 'examples': []},
            'rare': {'count': 0, 'percentage': 0.0, 'examples': []}
        }

    # Calculate thresholds
    frequencies = sorted(word_freq.values(), reverse=True)
    total_words = sum(frequencies)

    # Top 20% by frequency = common
    # Next 40% = uncommon
    # Bottom 40% = rare
    threshold_common = frequencies[int(len(frequencies) * 0.2)] if len(frequencies) > 5 else 10
    threshold_rare = frequencies[int(len(frequencies) * 0.6)] if len(frequencies) > 5 else 2

    common = []
    uncommon = []
    rare = []

    for word, freq in word_freq.items():
        if freq >= threshold_common or word.lower() in COMMON_WORDS:
            common.append({'word': word, 'frequency': freq})
        elif freq <= threshold_rare:
            rare.append({'word': word, 'frequency': freq})
        else:
            uncommon.append({'word': word, 'frequency': freq})

    return {
        'common': {
            'count': len(common),
            'percentage': round(len(common) / len(word_freq) * 100, 2),
            'examples': sorted(common, key=lambda x: x['frequency'], reverse=True)[:20]
        },
        'uncommon': {
            'count': len(uncommon),
            'percentage': round(len(uncommon) / len(word_freq) * 100, 2),
            'examples': sorted(uncommon, key=lambda x: x['frequency'], reverse=True)[:20]
        },
        'rare': {
            'count': len(rare),
            'percentage': round(len(rare) / len(word_freq) * 100, 2),
            'examples': sorted(rare, key=lambda x: x['frequency'])[:20]
        }
    }


def estimate_reading_level():
    """Estimate reading level using simple metrics"""
    if not GOODBOOK_DB.exists():
        return {}

    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    # Sample verses for analysis
    cursor.execute("SELECT text FROM verses WHERE text IS NOT NULL LIMIT 1000")

    total_sentences = 0
    total_words = 0
    total_syllables = 0

    for (text,) in cursor.fetchall():
        # Count sentences (rough approximation)
        sentences = len(re.split(r'[.!?]+', text))
        total_sentences += sentences

        # Count words
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        total_words += len(words)

        # Estimate syllables (rough approximation)
        for word in words:
            # Count vowel groups as syllable estimate
            syllables = len(re.findall(r'[aeiouy]+', word.lower()))
            total_syllables += max(1, syllables)  # At least 1 syllable per word

    conn.close()

    # Calculate metrics
    avg_words_per_sentence = total_words / total_sentences if total_sentences > 0 else 0
    avg_syllables_per_word = total_syllables / total_words if total_words > 0 else 0

    # Flesch-Kincaid Grade Level (simplified)
    # 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
    grade_level = (0.39 * avg_words_per_sentence) + (11.8 * avg_syllables_per_word) - 15.59

    return {
        'estimated_grade_level': round(grade_level, 1),
        'average_words_per_sentence': round(avg_words_per_sentence, 1),
        'average_syllables_per_word': round(avg_syllables_per_word, 2),
        'sample_size': 1000
    }


def analyze_greek_hebrew_terms():
    """Count Greek and Hebrew transliterations"""
    greek_count = 0
    hebrew_count = 0
    transliterations = []

    # From GoodBook.db
    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT language, COUNT(*) as count, transliteration
            FROM lexical_words
            WHERE transliteration IS NOT NULL
            GROUP BY language, transliteration
        """)

        for lang, count, trans in cursor.fetchall():
            if lang == 'Hebrew':
                hebrew_count += count
                if len(transliterations) < 20:
                    transliterations.append({'language': 'Hebrew', 'transliteration': trans})
            elif lang == 'Greek':
                greek_count += count
                if len(transliterations) < 40:
                    transliterations.append({'language': 'Greek', 'transliteration': trans})

        conn.close()

    # From concordance.db
    if CONCORDANCE_DB.exists():
        conn = sqlite3.connect(CONCORDANCE_DB)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT transliteration, COUNT(*) as count
            FROM strongs_lexicon
            WHERE transliteration IS NOT NULL AND strong_norm LIKE 'H%'
        """)
        hebrew_count += sum(count for trans, count in cursor.fetchall())

        cursor.execute("""
            SELECT transliteration, COUNT(*) as count
            FROM strongs_lexicon
            WHERE transliteration IS NOT NULL AND strong_norm LIKE 'G%'
        """)
        greek_count += sum(count for trans, count in cursor.fetchall())

        conn.close()

    return {
        'hebrew_terms': hebrew_count,
        'greek_terms': greek_count,
        'total_original_language_terms': hebrew_count + greek_count,
        'sample_transliterations': transliterations[:30]
    }


def identify_seminary_terms():
    """Identify theological/seminary-level terminology"""
    seminary_terms = {
        'atonement': 0, 'propitiation': 0, 'justification': 0, 'sanctification': 0,
        'regeneration': 0, 'glorification': 0, 'eschatology': 0, 'christology': 0,
        'soteriology': 0, 'pneumatology': 0, 'ecclesiology': 0, 'anthropology': 0,
        'predestination': 0, 'election': 0, 'reprobation': 0, 'imputation': 0,
        'transubstantiation': 0, 'consubstantiation': 0, 'incarnation': 0,
        'theophany': 0, 'epiphany': 0, 'exegesis': 0, 'hermeneutics': 0,
        'typology': 0, 'allegory': 0, 'apocalyptic': 0, 'messianic': 0
    }

    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        for term in seminary_terms.keys():
            cursor.execute(f"SELECT COUNT(*) FROM verses WHERE LOWER(text) LIKE '%{term}%'")
            count = cursor.fetchone()[0]
            seminary_terms[term] = count

        conn.close()

    # Sort by frequency
    sorted_terms = sorted(seminary_terms.items(), key=lambda x: x[1], reverse=True)
    found_terms = [(term, count) for term, count in sorted_terms if count > 0]

    return {
        'total_seminary_terms_found': len(found_terms),
        'terms_by_frequency': found_terms[:20],
        'all_terms_searched': list(seminary_terms.keys())
    }


def calculate_difficulty_distribution(word_freq_classification):
    """Calculate overall difficulty distribution"""
    common_pct = word_freq_classification['common']['percentage']
    uncommon_pct = word_freq_classification['uncommon']['percentage']
    rare_pct = word_freq_classification['rare']['percentage']

    # Simplified difficulty scoring
    # Easy: >60% common words
    # Medium: 40-60% common words
    # Hard: <40% common words

    if common_pct > 60:
        overall_difficulty = 'Easy'
    elif common_pct > 40:
        overall_difficulty = 'Medium'
    else:
        overall_difficulty = 'Hard'

    return {
        'easy_percentage': common_pct,
        'medium_percentage': uncommon_pct,
        'hard_percentage': rare_pct,
        'overall_difficulty': overall_difficulty
    }


def main():
    """Main analysis function"""
    print("Starting Difficulty & Accessibility Profile Analysis...")
    print(f"Output will be saved to: {OUTPUT_FILE}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Perform analyses
    print("\n1. Calculating word frequencies...")
    word_freq = get_word_frequencies()
    print(f"   -> Analyzed {sum(word_freq.values()):,} total words")
    print(f"   -> Found {len(word_freq):,} unique words")

    print("\n2. Classifying words by frequency (common/uncommon/rare)...")
    word_classification: Dict[str, Dict[str, Any]] = classify_words_by_frequency(word_freq)
    print(f"   -> Common: {word_classification['common']['count']:,} ({word_classification['common']['percentage']}%)")
    print(f"   -> Uncommon: {word_classification['uncommon']['count']:,} ({word_classification['uncommon']['percentage']}%)")
    print(f"   -> Rare: {word_classification['rare']['count']:,} ({word_classification['rare']['percentage']}%)")

    print("\n3. Estimating reading level...")
    reading_level = estimate_reading_level()
    print(f"   -> Estimated grade level: {reading_level.get('estimated_grade_level', 'N/A')}")

    print("\n4. Analyzing Greek/Hebrew transliterations...")
    greek_hebrew = analyze_greek_hebrew_terms()
    print(f"   -> Hebrew terms: {greek_hebrew['hebrew_terms']:,}")
    print(f"   -> Greek terms: {greek_hebrew['greek_terms']:,}")

    print("\n5. Identifying seminary-level terminology...")
    seminary = identify_seminary_terms()
    print(f"   -> Found {seminary['total_seminary_terms_found']} seminary terms")

    print("\n6. Calculating difficulty distribution...")
    difficulty_dist = calculate_difficulty_distribution(word_classification)
    print(f"   -> Overall difficulty: {difficulty_dist['overall_difficulty']}")

    # Compile results
    results = {
        'metadata': {
            'analysis_date': datetime.now().isoformat(),
            'databases_analyzed': {
                'goodbook_db': str(GOODBOOK_DB),
                'concordance_db': str(CONCORDANCE_DB)
            }
        },
        'word_frequency_classification': word_classification,
        'reading_level': reading_level,
        'greek_hebrew_terms': greek_hebrew,
        'seminary_terminology': seminary,
        'difficulty_distribution': difficulty_dist
    }

    # Save to JSON
    print(f"\n7. Saving results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n[DONE] Difficulty & Accessibility Profile Analysis Complete!")
    print(f"  Output: {OUTPUT_FILE}")

    return results


if __name__ == "__main__":
    main()
