#!/usr/bin/env python3
"""
Cross-Reference Verification Report
Validates theological connections and coverage quality
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
GOODBOOK_DB = PROJECT_ROOT / "data" / "GoodBook.db"
OUTPUT_DIR = PROJECT_ROOT / "output" / "Analytics"
OUTPUT_FILE = OUTPUT_DIR / "crossref_verification_report.json"


def get_verse_id_by_reference(cursor, book, chapter, verse):
    """Get verse ID from book/chapter/verse reference"""
    cursor.execute("""
        SELECT v.id
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        WHERE b.book_name = ? AND c.chapter_number = ? AND v.verse_number = ?
    """, (book, chapter, verse))
    result = cursor.fetchone()
    return result[0] if result else None


def get_verse_reference(cursor, verse_id):
    """Get book/chapter/verse reference from verse ID"""
    cursor.execute("""
        SELECT b.book_name, c.chapter_number, v.verse_number
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        WHERE v.id = ?
    """, (verse_id,))
    result = cursor.fetchone()
    return f"{result[0]} {result[1]}:{result[2]}" if result else f"Verse ID {verse_id}"


def calculate_coverage():
    """Calculate what percentage of Bible verses have connections"""
    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    # Total verses in Bible
    cursor.execute("SELECT COUNT(*) FROM verses")
    total_verses = cursor.fetchone()[0]

    # Verses with outgoing connections
    cursor.execute("SELECT COUNT(DISTINCT source_verse_id) FROM cross_references")
    verses_with_outgoing = cursor.fetchone()[0]

    # Verses with incoming connections
    cursor.execute("SELECT COUNT(DISTINCT related_verse_id) FROM cross_references")
    verses_with_incoming = cursor.fetchone()[0]

    # Verses with any connections (incoming or outgoing)
    cursor.execute("""
        SELECT COUNT(DISTINCT verse_id)
        FROM (
            SELECT source_verse_id as verse_id FROM cross_references
            UNION
            SELECT related_verse_id as verse_id FROM cross_references
        )
    """)
    verses_with_any = cursor.fetchone()[0]

    conn.close()

    return {
        'total_bible_verses': total_verses,
        'verses_with_outgoing': verses_with_outgoing,
        'verses_with_incoming': verses_with_incoming,
        'verses_with_any_connections': verses_with_any,
        'coverage_percentage': round((verses_with_any / total_verses) * 100, 2),
        'verses_without_connections': total_verses - verses_with_any
    }


def check_high_value_verses():
    """Check connections for theologically significant verses"""
    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    high_value_verses = [
        {"ref": "Genesis 1:1", "book": "Genesis", "chapter": 1, "verse": 1, "theme": "Creation"},
        {"ref": "Genesis 3:15", "book": "Genesis", "chapter": 3, "verse": 15, "theme": "Protoevangelium"},
        {"ref": "Psalm 22:1", "book": "Psalms", "chapter": 22, "verse": 1, "theme": "Messianic suffering"},
        {"ref": "Isaiah 53:5", "book": "Isaiah", "chapter": 53, "verse": 5, "theme": "Suffering Servant"},
        {"ref": "Isaiah 7:14", "book": "Isaiah", "chapter": 7, "verse": 14, "theme": "Virgin birth prophecy"},
        {"ref": "Micah 5:2", "book": "Micah", "chapter": 5, "verse": 2, "theme": "Bethlehem prophecy"},
        {"ref": "Matthew 1:1", "book": "Matthew", "chapter": 1, "verse": 1, "theme": "Jesus' genealogy"},
        {"ref": "John 1:1", "book": "John", "chapter": 1, "verse": 1, "theme": "Divine Word"},
        {"ref": "John 3:16", "book": "John", "chapter": 3, "verse": 16, "theme": "Gospel core"},
        {"ref": "Romans 3:23", "book": "Romans", "chapter": 3, "verse": 23, "theme": "Universal sin"},
        {"ref": "Romans 6:23", "book": "Romans", "chapter": 6, "verse": 23, "theme": "Wages of sin"},
        {"ref": "Ephesians 2:8", "book": "Ephesians", "chapter": 2, "verse": 8, "theme": "Salvation by grace"},
        {"ref": "Philippians 2:10", "book": "Philippians", "chapter": 2, "verse": 10, "theme": "Every knee bows"},
        {"ref": "Revelation 22:20", "book": "Revelation", "chapter": 22, "verse": 20, "theme": "Christ's return"}
    ]

    results = []
    for verse_info in high_value_verses:
        verse_id = get_verse_id_by_reference(cursor, verse_info['book'], verse_info['chapter'], verse_info['verse'])

        if verse_id:
            # Count outgoing connections
            cursor.execute("""
                SELECT COUNT(*) FROM cross_references
                WHERE source_verse_id = ?
            """, (verse_id,))
            outgoing = cursor.fetchone()[0]

            # Count incoming connections
            cursor.execute("""
                SELECT COUNT(*) FROM cross_references
                WHERE related_verse_id = ?
            """, (verse_id,))
            incoming = cursor.fetchone()[0]

            # Get sample connections (outgoing)
            cursor.execute("""
                SELECT related_verse_id FROM cross_references
                WHERE source_verse_id = ?
                LIMIT 5
            """, (verse_id,))
            sample_targets = [get_verse_reference(cursor, row[0]) for row in cursor.fetchall()]

            results.append({
                'reference': verse_info['ref'],
                'theme': verse_info['theme'],
                'verse_id': verse_id,
                'outgoing_connections': outgoing,
                'incoming_connections': incoming,
                'total_connections': outgoing + incoming,
                'sample_connections': sample_targets
            })
        else:
            results.append({
                'reference': verse_info['ref'],
                'theme': verse_info['theme'],
                'verse_id': None,
                'error': 'Verse not found in database'
            })

    conn.close()
    return results


def get_bidirectional_examples():
    """Find examples of bidirectional connections"""
    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            cr1.source_verse_id,
            cr1.related_verse_id
        FROM cross_references cr1
        WHERE EXISTS (
            SELECT 1 FROM cross_references cr2
            WHERE cr2.source_verse_id = cr1.related_verse_id
            AND cr2.related_verse_id = cr1.source_verse_id
        )
        LIMIT 10
    """)

    examples = []
    for source_id, target_id in cursor.fetchall():
        source_ref = get_verse_reference(cursor, source_id)
        target_ref = get_verse_reference(cursor, target_id)
        examples.append({
            'verse_a': source_ref,
            'verse_b': target_ref,
            'relationship': 'bidirectional'
        })

    conn.close()
    return examples


def get_unidirectional_examples():
    """Find examples of unidirectional connections"""
    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            cr1.source_verse_id,
            cr1.related_verse_id
        FROM cross_references cr1
        WHERE NOT EXISTS (
            SELECT 1 FROM cross_references cr2
            WHERE cr2.source_verse_id = cr1.related_verse_id
            AND cr2.related_verse_id = cr1.source_verse_id
        )
        LIMIT 10
    """)

    examples = []
    for source_id, target_id in cursor.fetchall():
        source_ref = get_verse_reference(cursor, source_id)
        target_ref = get_verse_reference(cursor, target_id)
        examples.append({
            'from_verse': source_ref,
            'to_verse': target_ref,
            'relationship': 'unidirectional (one-way)'
        })

    conn.close()
    return examples


def validate_theological_connections():
    """Validate major theological connections"""
    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    validations = []

    # 1. Isaiah 53 to Gospel accounts (Suffering Servant prophecy)
    isa53_id = get_verse_id_by_reference(cursor, "Isaiah", 53, 5)
    if isa53_id:
        cursor.execute("""
            SELECT COUNT(*) FROM cross_references cr
            JOIN verses v ON cr.related_verse_id = v.id
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE cr.source_verse_id = ?
            AND b.book_name IN ('Matthew', 'Mark', 'Luke', 'John')
        """, (isa53_id,))
        gospel_connections = cursor.fetchone()[0]

        # Get specific examples
        cursor.execute("""
            SELECT v.id FROM cross_references cr
            JOIN verses v ON cr.related_verse_id = v.id
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE cr.source_verse_id = ?
            AND b.book_name IN ('Matthew', 'Mark', 'Luke', 'John')
            LIMIT 5
        """, (isa53_id,))
        gospel_examples = [get_verse_reference(cursor, row[0]) for row in cursor.fetchall()]

        validations.append({
            'test': 'Isaiah 53 → Gospel Accounts',
            'description': 'Suffering Servant prophecy to fulfillment',
            'connections_found': gospel_connections,
            'status': 'PASS' if gospel_connections > 0 else 'FAIL',
            'examples': gospel_examples
        })

    # 2. Genesis 3:15 to Revelation (First and last enemy defeat)
    gen315_id = get_verse_id_by_reference(cursor, "Genesis", 3, 15)
    if gen315_id:
        cursor.execute("""
            SELECT COUNT(*) FROM cross_references cr
            JOIN verses v ON cr.related_verse_id = v.id
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE cr.source_verse_id = ?
            AND b.book_name = 'Revelation'
        """, (gen315_id,))
        rev_connections = cursor.fetchone()[0]

        cursor.execute("""
            SELECT v.id FROM cross_references cr
            JOIN verses v ON cr.related_verse_id = v.id
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE cr.source_verse_id = ?
            AND b.book_name = 'Revelation'
            LIMIT 5
        """, (gen315_id,))
        rev_examples = [get_verse_reference(cursor, row[0]) for row in cursor.fetchall()]

        validations.append({
            'test': 'Genesis 3:15 → Revelation',
            'description': 'Protoevangelium to final victory',
            'connections_found': rev_connections,
            'status': 'PASS' if rev_connections > 0 else 'FAIL',
            'examples': rev_examples
        })

    # 3. Micah 5:2 to Matthew 2 (Bethlehem prophecy)
    micah52_id = get_verse_id_by_reference(cursor, "Micah", 5, 2)
    if micah52_id:
        cursor.execute("""
            SELECT COUNT(*) FROM cross_references cr
            JOIN verses v ON cr.related_verse_id = v.id
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE cr.source_verse_id = ?
            AND b.book_name = 'Matthew' AND c.chapter_number = 2
        """, (micah52_id,))
        matt2_connections = cursor.fetchone()[0]

        cursor.execute("""
            SELECT v.id FROM cross_references cr
            JOIN verses v ON cr.related_verse_id = v.id
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE cr.source_verse_id = ?
            AND b.book_name = 'Matthew' AND c.chapter_number = 2
            LIMIT 3
        """, (micah52_id,))
        matt2_examples = [get_verse_reference(cursor, row[0]) for row in cursor.fetchall()]

        validations.append({
            'test': 'Micah 5:2 → Matthew 2',
            'description': 'Bethlehem birth prophecy to fulfillment',
            'connections_found': matt2_connections,
            'status': 'PASS' if matt2_connections > 0 else 'FAIL',
            'examples': matt2_examples
        })

    # 4. Psalm 22 to Crucifixion accounts
    ps22_id = get_verse_id_by_reference(cursor, "Psalms", 22, 1)
    if ps22_id:
        cursor.execute("""
            SELECT COUNT(*) FROM cross_references cr
            JOIN verses v ON cr.related_verse_id = v.id
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE cr.source_verse_id = ?
            AND b.book_name IN ('Matthew', 'Mark', 'Luke', 'John')
            AND c.chapter_number >= 26  -- Crucifixion chapters
        """, (ps22_id,))
        crucifixion_connections = cursor.fetchone()[0]

        cursor.execute("""
            SELECT v.id FROM cross_references cr
            JOIN verses v ON cr.related_verse_id = v.id
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE cr.source_verse_id = ?
            AND b.book_name IN ('Matthew', 'Mark', 'Luke', 'John')
            AND c.chapter_number >= 26
            LIMIT 5
        """, (ps22_id,))
        crucifixion_examples = [get_verse_reference(cursor, row[0]) for row in cursor.fetchall()]

        validations.append({
            'test': 'Psalm 22 → Crucifixion Accounts',
            'description': 'Prophetic suffering to fulfillment',
            'connections_found': crucifixion_connections,
            'status': 'PASS' if crucifixion_connections > 0 else 'FAIL',
            'examples': crucifixion_examples
        })

    # 5. OT Law to Jesus' teaching
    cursor.execute("""
        SELECT COUNT(*) FROM cross_references cr
        JOIN verses v1 ON cr.source_verse_id = v1.id
        JOIN chapters c1 ON v1.chapter_id = c1.id
        JOIN books b1 ON c1.book_id = b1.id
        JOIN verses v2 ON cr.related_verse_id = v2.id
        JOIN chapters c2 ON v2.chapter_id = c2.id
        JOIN books b2 ON c2.book_id = b2.id
        WHERE b1.book_name IN ('Exodus', 'Leviticus', 'Deuteronomy')
        AND b2.book_name IN ('Matthew', 'Mark', 'Luke', 'John')
    """)
    law_to_gospels = cursor.fetchone()[0]

    validations.append({
        'test': 'OT Law → Gospel Teaching',
        'description': 'Mosaic Law to Jesus\' interpretation',
        'connections_found': law_to_gospels,
        'status': 'PASS' if law_to_gospels > 0 else 'FAIL',
        'examples': []
    })

    conn.close()
    return validations


def main():
    """Main verification function"""
    print("Starting Cross-Reference Verification Report...")
    print(f"Output will be saved to: {OUTPUT_FILE}\n")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Coverage Analysis
    print("1. Calculating coverage statistics...")
    coverage = calculate_coverage()
    print(f"   -> Total verses: {coverage['total_bible_verses']:,}")
    print(f"   -> Verses with connections: {coverage['verses_with_any_connections']:,}")
    print(f"   -> Coverage: {coverage['coverage_percentage']}%")

    # 2. High-Value Verses
    print("\n2. Checking high-value theological verses...")
    high_value = check_high_value_verses()
    with_connections = sum(1 for v in high_value if v.get('total_connections', 0) > 0)
    print(f"   -> {with_connections}/{len(high_value)} key verses have connections")

    # 3. Bidirectional Examples
    print("\n3. Finding bidirectional connection examples...")
    bidirectional = get_bidirectional_examples()
    print(f"   -> Found {len(bidirectional)} bidirectional examples")

    # 4. Unidirectional Examples
    print("\n4. Finding unidirectional connection examples...")
    unidirectional = get_unidirectional_examples()
    print(f"   -> Found {len(unidirectional)} unidirectional examples")

    # 5. Theological Validation
    print("\n5. Validating theological connections...")
    theological = validate_theological_connections()
    passed = sum(1 for t in theological if t['status'] == 'PASS')
    print(f"   -> {passed}/{len(theological)} theological tests passed")

    # Compile report
    report = {
        'metadata': {
            'verification_date': datetime.now().isoformat(),
            'database': str(GOODBOOK_DB)
        },
        'coverage_analysis': coverage,
        'high_value_verses': high_value,
        'bidirectional_examples': bidirectional,
        'unidirectional_examples': unidirectional,
        'theological_validation': theological,
        'overall_assessment': {
            'coverage_grade': 'A' if coverage['coverage_percentage'] > 90 else 'B' if coverage['coverage_percentage'] > 80 else 'C',
            'theological_validity': 'PASS' if passed == len(theological) else 'PARTIAL',
            'data_richness': 'HIGH' if coverage['verses_with_any_connections'] > 29000 else 'MEDIUM'
        }
    }

    # Save report
    print(f"\n6. Saving verification report to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    print(f"\nCoverage: {coverage['coverage_percentage']}% of Bible ({coverage['verses_with_any_connections']:,}/{coverage['total_bible_verses']:,} verses)")
    print(f"High-Value Verses: {with_connections}/{len(high_value)} have connections")
    print(f"Theological Tests: {passed}/{len(theological)} passed")
    print(f"\nOverall Grade: {report['overall_assessment']['coverage_grade']}")
    print(f"Theological Validity: {report['overall_assessment']['theological_validity']}")
    print(f"Data Richness: {report['overall_assessment']['data_richness']}")

    print(f"\n{'='*70}\n")
    print("[DONE] Verification Report Complete!")
    print(f"  Output: {OUTPUT_FILE}")

    return report


if __name__ == "__main__":
    main()
