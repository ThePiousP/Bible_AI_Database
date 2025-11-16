#!/usr/bin/env python3
"""
Cross-Reference Data Validation Investigation
Comprehensive analysis to understand the 614,180 cross-reference count
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
GOODBOOK_DB = PROJECT_ROOT / "data" / "GoodBook.db"
OUTPUT_DIR = PROJECT_ROOT / "output" / "Analytics"
OUTPUT_FILE = OUTPUT_DIR / "crossref_validation_report.json"

def get_schema_info():
    """Get table schema information"""
    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(cross_references)")
    schema = cursor.fetchall()

    cursor.execute("SELECT * FROM cross_references LIMIT 20")
    samples = cursor.fetchall()

    conn.close()

    return {
        'columns': [{'cid': c[0], 'name': c[1], 'type': c[2], 'notnull': c[3], 'dflt_value': c[4], 'pk': c[5]} for c in schema],
        'sample_records': samples[:5]  # Just show first 5
    }


def check_bidirectional_storage():
    """Check if connections are stored in both directions"""
    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    # Count bidirectional pairs
    cursor.execute("""
        SELECT COUNT(*) as bidirectional_count
        FROM cross_references cr1
        WHERE EXISTS (
            SELECT 1 FROM cross_references cr2
            WHERE cr2.source_verse_id = cr1.related_verse_id
            AND cr2.related_verse_id = cr1.source_verse_id
        )
    """)
    bidirectional_count = cursor.fetchone()[0]

    # Total count
    cursor.execute("SELECT COUNT(*) FROM cross_references")
    total_count = cursor.fetchone()[0]

    # Percentage
    bidirectional_percentage = (bidirectional_count / total_count * 100) if total_count > 0 else 0

    conn.close()

    return {
        'bidirectional_count': bidirectional_count,
        'total_count': total_count,
        'bidirectional_percentage': round(bidirectional_percentage, 2),
        'estimated_unique_if_all_bidirectional': bidirectional_count // 2
    }


def check_duplicates():
    """Check for exact duplicate entries"""
    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    # Find duplicates
    cursor.execute("""
        SELECT
            source_verse_id,
            related_verse_id,
            COUNT(*) as duplicate_count
        FROM cross_references
        GROUP BY source_verse_id, related_verse_id
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC
        LIMIT 50
    """)
    duplicate_examples = cursor.fetchall()

    # Total duplicates
    cursor.execute("""
        SELECT
            COALESCE(SUM(cnt - 1), 0) as total_duplicates
        FROM (
            SELECT COUNT(*) as cnt
            FROM cross_references
            GROUP BY source_verse_id, related_verse_id
            HAVING COUNT(*) > 1
        )
    """)
    total_duplicates = cursor.fetchone()[0]

    conn.close()

    return {
        'total_duplicate_records': total_duplicates,
        'unique_duplicate_pairs': len(duplicate_examples),
        'sample_duplicates': duplicate_examples[:10]
    }


def check_self_references():
    """Check for verses that reference themselves"""
    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as self_reference_count
        FROM cross_references
        WHERE source_verse_id = related_verse_id
    """)
    self_ref_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT source_verse_id, related_verse_id
        FROM cross_references
        WHERE source_verse_id = related_verse_id
        LIMIT 20
    """)
    self_ref_examples = cursor.fetchall()

    conn.close()

    return {
        'self_reference_count': self_ref_count,
        'sample_self_references': self_ref_examples[:10]
    }


def analyze_connection_distribution():
    """Analyze distribution of connections per verse"""
    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    # Verses with most outgoing connections
    cursor.execute("""
        SELECT
            source_verse_id,
            COUNT(*) as connection_count
        FROM cross_references
        GROUP BY source_verse_id
        ORDER BY connection_count DESC
        LIMIT 50
    """)
    top_connected = cursor.fetchall()

    # Get verse details for top 10
    top_verse_ids = [v[0] for v in top_connected[:10]]
    if top_verse_ids:
        placeholders = ','.join('?' * len(top_verse_ids))
        cursor.execute(f"""
            SELECT
                v.id,
                b.book_name,
                c.chapter_number,
                v.verse_number
            FROM verses v
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE v.id IN ({placeholders})
        """, top_verse_ids)
        verse_details = {row[0]: f"{row[1]} {row[2]}:{row[3]}" for row in cursor.fetchall()}
    else:
        verse_details = {}

    # Connection count distribution
    cursor.execute("""
        SELECT
            connection_count,
            COUNT(*) as verses_with_this_count
        FROM (
            SELECT source_verse_id, COUNT(*) as connection_count
            FROM cross_references
            GROUP BY source_verse_id
        )
        GROUP BY connection_count
        ORDER BY connection_count DESC
        LIMIT 20
    """)
    distribution = cursor.fetchall()

    # Average connections per verse
    cursor.execute("""
        SELECT
            COUNT(*) * 1.0 / (SELECT COUNT(DISTINCT source_verse_id) FROM cross_references)
            as avg_connections_per_verse
    """)
    avg_connections = cursor.fetchone()[0]

    # Distinct verse counts
    cursor.execute("SELECT COUNT(DISTINCT source_verse_id) FROM cross_references")
    distinct_source = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT related_verse_id) FROM cross_references")
    distinct_target = cursor.fetchone()[0]

    conn.close()

    # Add verse details to top connected
    top_connected_with_details = [
        {
            'verse_id': v[0],
            'reference': verse_details.get(v[0], f'Verse ID {v[0]}'),
            'connection_count': v[1]
        }
        for v in top_connected[:10]
    ]

    return {
        'top_connected_verses': top_connected_with_details,
        'connection_distribution': dict(distribution),
        'avg_connections_per_verse': round(avg_connections, 2),
        'distinct_source_verses': distinct_source,
        'distinct_target_verses': distinct_target
    }


def calculate_unique_connections():
    """Calculate truly unique connections (treating A->B and B->A as same)"""
    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    # Get all connections
    cursor.execute("""
        SELECT DISTINCT source_verse_id, related_verse_id
        FROM cross_references
    """)
    all_connections = cursor.fetchall()

    # Create unique pairs (treating bidirectional as one)
    unique_pairs = set()
    for source, target in all_connections:
        # Always store as (smaller_id, larger_id) to avoid duplicates
        pair = tuple(sorted([source, target]))
        unique_pairs.add(pair)

    conn.close()

    return {
        'raw_distinct_directional': len(all_connections),
        'unique_logical_connections': len(unique_pairs)
    }


def assess_data_quality(metrics):
    """Assess overall data quality and provide recommendations"""

    # Calculate clean connection count
    raw_total = metrics['schema']['total_raw_count']
    duplicates = metrics['duplicates']['total_duplicate_records']
    self_refs = metrics['self_references']['self_reference_count']
    unique_logical = metrics['unique_connections']['unique_logical_connections']

    # Determine status
    if unique_logical >= 340000 and unique_logical <= 382000:
        status = "GREEN"
        assessment = "Matches CrossWire expected range"
    elif unique_logical > 382000:
        status = "YELLOW"
        assessment = f"Higher than expected ({unique_logical:,} vs 340k-382k range)"
    else:
        status = "YELLOW"
        assessment = f"Lower than expected ({unique_logical:,} vs 340k-382k range)"

    # Storage method
    bid_pct = metrics['bidirectional']['bidirectional_percentage']
    if bid_pct > 95:
        storage_method = "Bidirectional (both A->B and B->A stored)"
    elif bid_pct > 80:
        storage_method = "Mostly bidirectional with some unidirectional"
    elif bid_pct > 20:
        storage_method = "Mixed bidirectional and unidirectional"
    else:
        storage_method = "Primarily unidirectional"

    # Calculate ratios
    ratio_to_crosswire_mid = unique_logical / 361000  # Midpoint of CrossWire range

    # Recommendations
    recommendations = []
    if duplicates > 0:
        recommendations.append(f"Remove {duplicates:,} duplicate entries")
    if self_refs > 0:
        recommendations.append(f"Remove {self_refs:,} self-references")
    if bid_pct > 95:
        recommendations.append("Consider storing only unidirectional pairs to save space (current: bidirectional)")

    if not recommendations:
        recommendations.append("No data cleaning required - database is clean")

    return {
        'status': status,
        'assessment': assessment,
        'storage_method': storage_method,
        'ratio_to_crosswire': round(ratio_to_crosswire_mid, 2),
        'clean_connection_count': raw_total - duplicates - self_refs,
        'unique_logical_connections': unique_logical,
        'recommendations': recommendations
    }


def main():
    """Main investigation function"""
    print("Starting Cross-Reference Validation Investigation...")
    print(f"Output will be saved to: {OUTPUT_FILE}\n")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Task 1: Schema Investigation
    print("1. Investigating database schema...")
    schema = get_schema_info()

    # Get total count
    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM cross_references")
    total_count = cursor.fetchone()[0]
    conn.close()
    schema['total_raw_count'] = total_count
    print(f"   -> Total raw records: {total_count:,}")

    # Task 2: Bidirectional Check
    print("\n2. Checking bidirectional storage...")
    bidirectional = check_bidirectional_storage()
    print(f"   -> Bidirectional entries: {bidirectional['bidirectional_count']:,} ({bidirectional['bidirectional_percentage']}%)")

    # Task 3: Duplicate Detection
    print("\n3. Detecting duplicates...")
    duplicates = check_duplicates()
    print(f"   -> Duplicate records: {duplicates['total_duplicate_records']:,}")

    # Task 4: Self-References
    print("\n4. Checking self-references...")
    self_refs = check_self_references()
    print(f"   -> Self-references: {self_refs['self_reference_count']:,}")

    # Task 5: Connection Distribution
    print("\n5. Analyzing connection distribution...")
    distribution = analyze_connection_distribution()
    print(f"   -> Distinct source verses: {distribution['distinct_source_verses']:,}")
    print(f"   -> Average connections per verse: {distribution['avg_connections_per_verse']}")
    print(f"   -> Top connected verse: {distribution['top_connected_verses'][0]['reference']} ({distribution['top_connected_verses'][0]['connection_count']} connections)")

    # Task 6: Calculate Unique Connections
    print("\n6. Calculating unique logical connections...")
    unique_conns = calculate_unique_connections()
    print(f"   -> Raw distinct directional: {unique_conns['raw_distinct_directional']:,}")
    print(f"   -> Unique logical connections: {unique_conns['unique_logical_connections']:,}")

    # Compile all metrics
    metrics = {
        'schema': schema,
        'bidirectional': bidirectional,
        'duplicates': duplicates,
        'self_references': self_refs,
        'distribution': distribution,
        'unique_connections': unique_conns
    }

    # Task 7: Data Quality Assessment
    print("\n7. Assessing data quality...")
    quality = assess_data_quality(metrics)
    print(f"   -> Status: {quality['status']}")
    print(f"   -> Assessment: {quality['assessment']}")
    print(f"   -> Storage method: {quality['storage_method']}")
    print(f"   -> Ratio to CrossWire: {quality['ratio_to_crosswire']}x")

    # Final report
    report = {
        'metadata': {
            'investigation_date': datetime.now().isoformat(),
            'database': str(GOODBOOK_DB)
        },
        'summary': {
            'raw_total': total_count,
            'duplicates': duplicates['total_duplicate_records'],
            'self_references': self_refs['self_reference_count'],
            'clean_directional': quality['clean_connection_count'],
            'unique_logical_connections': unique_conns['unique_logical_connections'],
            'bidirectional_percentage': bidirectional['bidirectional_percentage']
        },
        'quality_assessment': quality,
        'detailed_metrics': metrics
    }

    # Save report
    print(f"\n8. Saving validation report to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*70)
    print("CROSS-REFERENCE VALIDATION SUMMARY")
    print("="*70)
    print(f"\nRaw Database Entries: {total_count:,}")
    print(f"After Removing Duplicates: {quality['clean_connection_count']:,}")
    print(f"Unique Logical Connections: {unique_conns['unique_logical_connections']:,}")
    print(f"\nStorage Method: {quality['storage_method']}")
    print(f"Data Quality Status: {quality['status']}")
    print(f"\nAssessment: {quality['assessment']}")

    if quality['recommendations']:
        print(f"\nRecommendations:")
        for rec in quality['recommendations']:
            print(f"  - {rec}")

    print(f"\n{'='*70}\n")
    print("[DONE] Cross-Reference Validation Complete!")
    print(f"  Output: {OUTPUT_FILE}")

    return report


if __name__ == "__main__":
    main()
