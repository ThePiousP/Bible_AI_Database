#!/usr/bin/env python3
"""
Cross-Reference Network Analysis
Analyzes verse cross-references, network metrics, connections, and theological hubs
"""

import sqlite3
import json
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime


# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
GOODBOOK_DB = PROJECT_ROOT / "data" / "GoodBook.db"
OUTPUT_DIR = PROJECT_ROOT / "output" / "Analytics"
OUTPUT_FILE = OUTPUT_DIR / "crossref_network.json"


def get_cross_references():
    """Extract all cross-references from database"""
    if not GOODBOOK_DB.exists():
        print(f"   Warning: Database not found at {GOODBOOK_DB}")
        return []

    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            cr.id,
            cr.source_verse_id,
            cr.related_verse_id
        FROM cross_references cr
    """)

    cross_refs = cursor.fetchall()
    conn.close()

    return cross_refs


def get_verse_details(verse_ids):
    """Get verse reference details for given verse IDs"""
    if not verse_ids or not GOODBOOK_DB.exists():
        return {}

    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(verse_ids))
    cursor.execute(f"""
        SELECT
            v.id,
            b.book_name,
            c.chapter_number,
            v.verse_number,
            SUBSTR(v.text, 1, 100) as text_preview
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        WHERE v.id IN ({placeholders})
    """, verse_ids)

    verse_details = {}
    for verse_id, book, chapter, verse, text in cursor.fetchall():
        verse_details[verse_id] = {
            'reference': f"{book} {chapter}:{verse}",
            'book': book,
            'chapter': chapter,
            'verse': verse,
            'text_preview': text
        }

    conn.close()
    return verse_details


def analyze_network_metrics(cross_refs):
    """Calculate network metrics for cross-reference graph"""
    # Count connections per verse
    connections_count = Counter()
    outgoing = defaultdict(set)
    incoming = defaultdict(set)

    for ref_id, source_id, target_id in cross_refs:
        connections_count[source_id] += 1
        connections_count[target_id] += 1
        outgoing[source_id].add(target_id)
        incoming[target_id].add(source_id)

    # Calculate statistics
    total_verses_with_refs = len(connections_count)
    total_connections = len(cross_refs)
    avg_connections = sum(connections_count.values()) / len(connections_count) if connections_count else 0

    # Find distribution
    connection_distribution = Counter(connections_count.values())

    return {
        'total_cross_references': total_connections,
        'total_verses_with_references': total_verses_with_refs,
        'average_connections_per_verse': round(avg_connections, 2),
        'max_connections': max(connections_count.values()) if connections_count else 0,
        'min_connections': min(connections_count.values()) if connections_count else 0,
        'connection_distribution': dict(connection_distribution),
        'connections_count': dict(connections_count),
        'outgoing': {k: list(v) for k, v in outgoing.items()},
        'incoming': {k: list(v) for k, v in incoming.items()}
    }


def find_most_connected_verses(network_metrics, top_n=50):
    """Identify the most connected verses (theological hubs)"""
    connections = network_metrics['connections_count']

    # Sort by connection count
    sorted_verses = sorted(connections.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # Get verse details
    verse_ids = [verse_id for verse_id, count in sorted_verses]
    verse_details = get_verse_details(verse_ids)

    most_connected = []
    for verse_id, count in sorted_verses:
        details = verse_details.get(verse_id, {})
        most_connected.append({
            'verse_id': verse_id,
            'reference': details.get('reference', f'Verse ID {verse_id}'),
            'connection_count': count,
            'text_preview': details.get('text_preview', '')
        })

    return most_connected


def find_isolated_verses():
    """Find verses with no cross-references"""
    if not GOODBOOK_DB.exists():
        return []

    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    # Find verses that don't appear in cross_references table
    cursor.execute("""
        SELECT
            v.id,
            b.book_name,
            c.chapter_number,
            v.verse_number,
            COUNT(cr.id) as ref_count
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        LEFT JOIN cross_references cr ON (v.id = cr.source_verse_id OR v.id = cr.related_verse_id)
        GROUP BY v.id, b.book_name, c.chapter_number, v.verse_number
        HAVING ref_count = 0
        LIMIT 100
    """)

    isolated = []
    for verse_id, book, chapter, verse, ref_count in cursor.fetchall():
        isolated.append({
            'verse_id': verse_id,
            'reference': f"{book} {chapter}:{verse}"
        })

    conn.close()
    return isolated


def analyze_testament_connections(cross_refs):
    """Analyze connections between Old Testament and New Testament"""
    # Get book testament mapping
    if not GOODBOOK_DB.exists():
        return {}

    conn = sqlite3.connect(GOODBOOK_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT v.id, b.testament
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        WHERE b.testament IS NOT NULL
    """)

    verse_testament = {}
    for verse_id, testament in cursor.fetchall():
        verse_testament[verse_id] = testament

    conn.close()

    # Count connections
    ot_to_ot = 0
    nt_to_nt = 0
    ot_to_nt = 0
    nt_to_ot = 0
    unknown = 0

    for ref_id, source_id, target_id in cross_refs:
        source_test = verse_testament.get(source_id)
        target_test = verse_testament.get(target_id)

        if source_test and target_test:
            if source_test == 'Old Testament' and target_test == 'Old Testament':
                ot_to_ot += 1
            elif source_test == 'New Testament' and target_test == 'New Testament':
                nt_to_nt += 1
            elif source_test == 'Old Testament' and target_test == 'New Testament':
                ot_to_nt += 1
            elif source_test == 'New Testament' and target_test == 'Old Testament':
                nt_to_ot += 1
        else:
            unknown += 1

    total = ot_to_ot + nt_to_nt + ot_to_nt + nt_to_ot
    return {
        'old_to_old': {
            'count': ot_to_ot,
            'percentage': round(ot_to_ot / total * 100, 2) if total > 0 else 0
        },
        'new_to_new': {
            'count': nt_to_nt,
            'percentage': round(nt_to_nt / total * 100, 2) if total > 0 else 0
        },
        'old_to_new': {
            'count': ot_to_nt,
            'percentage': round(ot_to_nt / total * 100, 2) if total > 0 else 0
        },
        'new_to_old': {
            'count': nt_to_ot,
            'percentage': round(nt_to_ot / total * 100, 2) if total > 0 else 0
        },
        'unknown': unknown
    }


def calculate_network_density(network_metrics):
    """Calculate network density metrics"""
    total_verses = network_metrics['total_verses_with_references']
    total_connections = network_metrics['total_cross_references']

    # Maximum possible connections in undirected graph
    max_possible = (total_verses * (total_verses - 1)) / 2 if total_verses > 1 else 0

    density = (total_connections / max_possible) if max_possible > 0 else 0

    return {
        'network_density': round(density, 6),
        'total_possible_connections': int(max_possible),
        'actual_connections': total_connections,
        'sparsity': round(1 - density, 6)
    }


def main():
    """Main analysis function"""
    print("Starting Cross-Reference Network Analysis...")
    print(f"Output will be saved to: {OUTPUT_FILE}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get cross-references
    print("\n1. Extracting cross-references from database...")
    cross_refs = get_cross_references()
    print(f"   -> Found {len(cross_refs):,} cross-references")

    if not cross_refs:
        print("\n[WARNING] Warning: No cross-references found. Analysis will be limited.")
        results = {
            'metadata': {
                'analysis_date': datetime.now().isoformat(),
                'database': str(GOODBOOK_DB)
            },
            'error': 'No cross-references found in database'
        }
    else:
        # Perform analyses
        print("\n2. Calculating network metrics...")
        network_metrics = analyze_network_metrics(cross_refs)
        print(f"   -> {network_metrics['total_verses_with_references']:,} verses have references")
        print(f"   -> Average {network_metrics['average_connections_per_verse']} connections per verse")

        print("\n3. Finding most connected verses (theological hubs)...")
        most_connected = find_most_connected_verses(network_metrics, top_n=50)
        print(f"   -> Top verse: {most_connected[0]['reference']} ({most_connected[0]['connection_count']} connections)")

        print("\n4. Finding isolated verses...")
        isolated = find_isolated_verses()
        print(f"   -> Found {len(isolated):,} isolated verses (sample of 100)")

        print("\n5. Analyzing testament connections (OT <-> NT)...")
        testament_conn = analyze_testament_connections(cross_refs)
        print(f"   -> OT -> NT: {testament_conn['old_to_new']['count']:,}")
        print(f"   -> NT -> OT: {testament_conn['new_to_old']['count']:,}")

        print("\n6. Calculating network density...")
        density = calculate_network_density(network_metrics)
        print(f"   -> Network density: {density['network_density']:.6f}")

        # Compile results (excluding large dictionaries for readability)
        results = {
            'metadata': {
                'analysis_date': datetime.now().isoformat(),
                'database': str(GOODBOOK_DB)
            },
            'summary': {
                'total_cross_references': network_metrics['total_cross_references'],
                'total_verses_with_references': network_metrics['total_verses_with_references'],
                'average_connections_per_verse': network_metrics['average_connections_per_verse'],
                'max_connections': network_metrics['max_connections'],
                'min_connections': network_metrics['min_connections']
            },
            'connection_distribution': network_metrics['connection_distribution'],
            'most_connected_verses': most_connected,
            'isolated_verses_sample': isolated,
            'testament_connections': testament_conn,
            'network_density': density
        }

    # Save to JSON
    print(f"\n7. Saving results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n[DONE] Cross-Reference Network Analysis Complete!")
    print(f"  Output: {OUTPUT_FILE}")

    return results


if __name__ == "__main__":
    main()
