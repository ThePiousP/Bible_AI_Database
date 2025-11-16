#!/usr/bin/env python3
"""
Completeness & Gap Analysis
Identifies missing data, gaps, duplicates, and consistency issues
"""

import sqlite3
import json
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime


# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
GOODBOOK_DB = PROJECT_ROOT / "data" / "GoodBook.db"
CONCORDANCE_DB = PROJECT_ROOT / "Folders" / "REFACTOR_BACKUPS" / "backup_2025-10-29_18-08-33" / "data" / "concordance.db"
OUTPUT_DIR = PROJECT_ROOT / "output" / "Analytics"
OUTPUT_FILE = OUTPUT_DIR / "completeness_report.json"


def check_missing_strongs_numbers():
    """Check for gaps in Strong's number sequences"""
    hebrew_numbers = set()
    greek_numbers = set()

    # From GoodBook.db
    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT strongs_number, language FROM lexical_words WHERE strongs_number IS NOT NULL")
        for strongs, lang in cursor.fetchall():
            if lang == 'Hebrew' and strongs:
                hebrew_numbers.add(strongs)
            elif lang == 'Greek' and strongs:
                greek_numbers.add(strongs)

        conn.close()

    # From concordance.db
    if CONCORDANCE_DB.exists():
        conn = sqlite3.connect(CONCORDANCE_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT strong_norm FROM strongs_lexicon WHERE strong_norm IS NOT NULL")
        for (strongs,) in cursor.fetchall():
            if strongs and strongs.startswith('H'):
                hebrew_numbers.add(strongs)
            elif strongs and strongs.startswith('G'):
                greek_numbers.add(strongs)

        conn.close()

    # Find gaps
    def find_gaps(numbers, prefix, max_num):
        nums = sorted([int(s[1:]) for s in numbers if s.startswith(prefix) and s[1:].isdigit()])
        if not nums:
            return []

        gaps = []
        for i in range(nums[0], min(nums[-1] + 1, max_num + 1)):
            if i not in nums:
                gaps.append(f"{prefix}{i:04d}")

        return gaps

    hebrew_gaps = find_gaps(hebrew_numbers, 'H', 8674)
    greek_gaps = find_gaps(greek_numbers, 'G', 5624)

    return {
        'hebrew': {
            'total_present': len([n for n in hebrew_numbers if n.startswith('H')]),
            'expected_max': 8674,
            'gaps_count': len(hebrew_gaps),
            'sample_gaps': hebrew_gaps[:50]
        },
        'greek': {
            'total_present': len([n for n in greek_numbers if n.startswith('G')]),
            'expected_max': 5624,
            'gaps_count': len(greek_gaps),
            'sample_gaps': greek_gaps[:50]
        }
    }


def check_underrepresented_books():
    """Find books with very little data"""
    if not GOODBOOK_DB.exists():
        return []

    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            b.book_name,
            COUNT(DISTINCT c.id) as chapter_count,
            COUNT(DISTINCT v.id) as verse_count,
            COUNT(vw.id) as word_count
        FROM books b
        LEFT JOIN chapters c ON c.book_id = b.id
        LEFT JOIN verses v ON v.chapter_id = c.id
        LEFT JOIN verse_words vw ON vw.verse_id = v.id
        GROUP BY b.book_name
        HAVING verse_count < 10 OR word_count < 100
    """)

    underrepresented = []
    for book, chapters, verses, words in cursor.fetchall():
        underrepresented.append({
            'book': book,
            'chapters': chapters,
            'verses': verses,
            'words': words,
            'issue': 'Very low data count'
        })

    conn.close()
    return underrepresented


def check_empty_fields():
    """Detect empty or null fields in critical tables"""
    issues = []

    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        # Check verses with no text
        cursor.execute("SELECT COUNT(*) FROM verses WHERE text IS NULL OR TRIM(text) = ''")
        empty_verses = cursor.fetchone()[0]
        if empty_verses > 0:
            issues.append({
                'table': 'verses',
                'field': 'text',
                'count': empty_verses,
                'severity': 'high'
            })

        # Check lexical_words with missing definitions
        cursor.execute("SELECT COUNT(*) FROM lexical_words WHERE definition IS NULL OR TRIM(definition) = ''")
        empty_definitions = cursor.fetchone()[0]
        if empty_definitions > 0:
            issues.append({
                'table': 'lexical_words',
                'field': 'definition',
                'count': empty_definitions,
                'severity': 'medium'
            })

        # Check books with no testament
        cursor.execute("SELECT COUNT(*) FROM books WHERE testament IS NULL OR TRIM(testament) = ''")
        empty_testament = cursor.fetchone()[0]
        if empty_testament > 0:
            issues.append({
                'table': 'books',
                'field': 'testament',
                'count': empty_testament,
                'severity': 'medium'
            })

        conn.close()

    return issues


def check_duplicate_entries():
    """Detect potential duplicate entries"""
    duplicates = []

    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        # Check for duplicate book names
        cursor.execute("""
            SELECT book_name, COUNT(*) as count
            FROM books
            GROUP BY book_name
            HAVING count > 1
        """)

        for book, count in cursor.fetchall():
            duplicates.append({
                'table': 'books',
                'field': 'book_name',
                'value': book,
                'count': count
            })

        # Check for duplicate Strong's numbers
        cursor.execute("""
            SELECT strongs_number, COUNT(*) as count
            FROM lexical_words
            GROUP BY strongs_number
            HAVING count > 1 AND strongs_number IS NOT NULL
        """)

        for strongs, count in cursor.fetchall():
            duplicates.append({
                'table': 'lexical_words',
                'field': 'strongs_number',
                'value': strongs,
                'count': count
            })

        conn.close()

    return duplicates


def check_data_consistency():
    """Check for data consistency issues"""
    consistency_issues = []

    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        # Check for orphaned verses (verses without valid chapter)
        cursor.execute("""
            SELECT COUNT(*)
            FROM verses v
            LEFT JOIN chapters c ON v.chapter_id = c.id
            WHERE c.id IS NULL
        """)
        orphaned_verses = cursor.fetchone()[0]
        if orphaned_verses > 0:
            consistency_issues.append({
                'issue': 'Orphaned verses (no matching chapter)',
                'count': orphaned_verses,
                'severity': 'high'
            })

        # Check for orphaned chapters (chapters without valid book)
        cursor.execute("""
            SELECT COUNT(*)
            FROM chapters c
            LEFT JOIN books b ON c.book_id = b.id
            WHERE b.id IS NULL
        """)
        orphaned_chapters = cursor.fetchone()[0]
        if orphaned_chapters > 0:
            consistency_issues.append({
                'issue': 'Orphaned chapters (no matching book)',
                'count': orphaned_chapters,
                'severity': 'high'
            })

        # Check for cross-references pointing to non-existent verses
        cursor.execute("""
            SELECT COUNT(*)
            FROM cross_references cr
            LEFT JOIN verses v ON cr.source_verse_id = v.id
            WHERE v.id IS NULL
        """)
        invalid_xrefs_source = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM cross_references cr
            LEFT JOIN verses v ON cr.related_verse_id = v.id
            WHERE v.id IS NULL
        """)
        invalid_xrefs_target = cursor.fetchone()[0]

        if invalid_xrefs_source > 0 or invalid_xrefs_target > 0:
            consistency_issues.append({
                'issue': 'Invalid cross-references (pointing to non-existent verses)',
                'count': invalid_xrefs_source + invalid_xrefs_target,
                'severity': 'medium'
            })

        conn.close()

    return consistency_issues


def validate_format():
    """Validate data format in key fields"""
    format_issues = []

    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        # Check Strong's number format (should be H#### or G####)
        cursor.execute("""
            SELECT strongs_number, COUNT(*) as count
            FROM lexical_words
            WHERE strongs_number IS NOT NULL
              AND strongs_number NOT LIKE 'H%'
              AND strongs_number NOT LIKE 'G%'
            GROUP BY strongs_number
        """)

        invalid_strongs = cursor.fetchall()
        if invalid_strongs:
            format_issues.append({
                'field': 'lexical_words.strongs_number',
                'issue': 'Invalid Strong\'s number format (should be H#### or G####)',
                'count': len(invalid_strongs),
                'sample': [s[0] for s in invalid_strongs[:10]]
            })

        conn.close()

    return format_issues


def calculate_coverage_percentage():
    """Calculate overall data coverage percentages"""
    coverage = {}

    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        # Books coverage (66 books in full Bible)
        cursor.execute("SELECT COUNT(DISTINCT book_name) FROM books")
        book_count = cursor.fetchone()[0]
        coverage['books'] = {
            'current': book_count,
            'expected': 66,
            'percentage': round(book_count / 66 * 100, 2)
        }

        # Verses coverage (31,102 verses in KJV)
        cursor.execute("SELECT COUNT(*) FROM verses")
        verse_count = cursor.fetchone()[0]
        coverage['verses'] = {
            'current': verse_count,
            'expected': 31102,
            'percentage': round(verse_count / 31102 * 100, 2)
        }

        # Cross-references coverage
        cursor.execute("SELECT COUNT(*) FROM cross_references")
        xref_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM verses")
        total_verses = cursor.fetchone()[0]
        coverage['cross_references'] = {
            'current': xref_count,
            'average_per_verse': round(xref_count / total_verses, 2) if total_verses > 0 else 0
        }

        conn.close()

    return coverage


def main():
    """Main analysis function"""
    print("Starting Completeness & Gap Analysis...")
    print(f"Output will be saved to: {OUTPUT_FILE}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Perform analyses
    print("\n1. Checking for missing Strong's numbers...")
    strongs_gaps = check_missing_strongs_numbers()
    print(f"   -> Hebrew gaps: {strongs_gaps['hebrew']['gaps_count']}")
    print(f"   -> Greek gaps: {strongs_gaps['greek']['gaps_count']}")

    print("\n2. Identifying underrepresented books...")
    underrep_books = check_underrepresented_books()
    print(f"   -> Found {len(underrep_books)} underrepresented books")

    print("\n3. Checking for empty/null fields...")
    empty_fields = check_empty_fields()
    print(f"   -> Found {len(empty_fields)} empty field issues")

    print("\n4. Detecting duplicate entries...")
    duplicates = check_duplicate_entries()
    print(f"   -> Found {len(duplicates)} duplicate entry issues")

    print("\n5. Checking data consistency...")
    consistency = check_data_consistency()
    print(f"   -> Found {len(consistency)} consistency issues")

    print("\n6. Validating data formats...")
    format_issues = validate_format()
    print(f"   -> Found {len(format_issues)} format issues")

    print("\n7. Calculating coverage percentages...")
    coverage = calculate_coverage_percentage()
    print(f"   -> Books: {coverage.get('books', {}).get('percentage', 0)}%")
    print(f"   -> Verses: {coverage.get('verses', {}).get('percentage', 0)}%")

    # Calculate overall health score
    total_issues = len(empty_fields) + len(duplicates) + len(consistency)
    if total_issues == 0:
        health_status = 'Excellent'
        health_score = 100
    elif total_issues <= 5:
        health_status = 'Good'
        health_score = 85
    elif total_issues <= 15:
        health_status = 'Fair'
        health_score = 70
    else:
        health_status = 'Needs Improvement'
        health_score = 50

    # Compile results
    results = {
        'metadata': {
            'analysis_date': datetime.now().isoformat(),
            'databases_analyzed': {
                'goodbook_db': str(GOODBOOK_DB),
                'concordance_db': str(CONCORDANCE_DB)
            }
        },
        'health_score': health_score,
        'health_status': health_status,
        'total_issues_found': total_issues,
        'strongs_gaps': strongs_gaps,
        'underrepresented_books': underrep_books,
        'empty_fields': empty_fields,
        'duplicate_entries': duplicates,
        'consistency_issues': consistency,
        'format_issues': format_issues,
        'coverage': coverage
    }

    # Save to JSON
    print(f"\n8. Saving results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n[DONE] Completeness & Gap Analysis Complete!")
    print(f"  Health Status: {health_status} (Score: {health_score}/100)")
    print(f"  Output: {OUTPUT_FILE}")

    return results


if __name__ == "__main__":
    main()
