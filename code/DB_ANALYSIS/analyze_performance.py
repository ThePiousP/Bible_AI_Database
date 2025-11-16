#!/usr/bin/env python3
"""
Performance Benchmarks Analysis
Tests query performance, database size, and optimization opportunities
"""

import sqlite3
import json
import time
import os
from pathlib import Path
from datetime import datetime


# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
GOODBOOK_DB = PROJECT_ROOT / "data" / "GoodBook.db"
CONCORDANCE_DB = PROJECT_ROOT / "Folders" / "REFACTOR_BACKUPS" / "backup_2025-10-29_18-08-33" / "data" / "concordance.db"
OUTPUT_DIR = PROJECT_ROOT / "output" / "Analytics"
OUTPUT_FILE = OUTPUT_DIR / "performance_metrics.json"


def get_database_size(db_path):
    """Get database file size in bytes"""
    if db_path.exists():
        size_bytes = os.path.getsize(db_path)
        size_mb = size_bytes / (1024 * 1024)
        size_gb = size_bytes / (1024 * 1024 * 1024)

        return {
            'bytes': size_bytes,
            'megabytes': round(size_mb, 2),
            'gigabytes': round(size_gb, 4),
            'human_readable': f"{size_mb:.2f} MB" if size_mb < 1024 else f"{size_gb:.2f} GB"
        }
    return None


def benchmark_query(conn, query, description, iterations=5):
    """Benchmark a SQL query multiple times and return statistics"""
    times = []

    for _ in range(iterations):
        start = time.time()
        cursor = conn.cursor()
        cursor.execute(query)
        cursor.fetchall()  # Ensure all results are fetched
        end = time.time()
        times.append((end - start) * 1000)  # Convert to milliseconds

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    return {
        'description': description,
        'query': query[:100] + '...' if len(query) > 100 else query,
        'iterations': iterations,
        'average_ms': round(avg_time, 3),
        'min_ms': round(min_time, 3),
        'max_ms': round(max_time, 3)
    }


def benchmark_goodbook_queries():
    """Benchmark common queries on GoodBook.db"""
    if not GOODBOOK_DB.exists():
        return []

    conn = sqlite3.connect(GOODBOOK_DB)
    benchmarks = []

    # Query 1: Simple book lookup
    benchmarks.append(benchmark_query(
        conn,
        "SELECT * FROM books WHERE book_name = 'Genesis'",
        "Simple book lookup by name"
    ))

    # Query 2: Verse search
    benchmarks.append(benchmark_query(
        conn,
        "SELECT v.text FROM verses v LIMIT 100",
        "Fetch 100 verses"
    ))

    # Query 3: Join across books, chapters, verses
    benchmarks.append(benchmark_query(
        conn,
        """
        SELECT b.book_name, c.chapter_number, v.verse_number, v.text
        FROM books b
        JOIN chapters c ON c.book_id = b.id
        JOIN verses v ON v.chapter_id = c.id
        LIMIT 1000
        """,
        "Join books, chapters, verses (1000 rows)"
    ))

    # Query 4: Cross-reference lookup
    benchmarks.append(benchmark_query(
        conn,
        "SELECT COUNT(*) FROM cross_references",
        "Count all cross-references"
    ))

    # Query 5: Lexical word search
    benchmarks.append(benchmark_query(
        conn,
        "SELECT * FROM lexical_words WHERE language = 'Greek' LIMIT 100",
        "Fetch 100 Greek lexical words"
    ))

    # Query 6: Full-text search simulation
    benchmarks.append(benchmark_query(
        conn,
        "SELECT * FROM verses WHERE text LIKE '%Jesus%' LIMIT 50",
        "Text search for 'Jesus' (LIKE query)"
    ))

    # Query 7: Aggregate query
    benchmarks.append(benchmark_query(
        conn,
        """
        SELECT b.book_name, COUNT(v.id) as verse_count
        FROM books b
        LEFT JOIN chapters c ON c.book_id = b.id
        LEFT JOIN verses v ON v.chapter_id = c.id
        GROUP BY b.book_name
        """,
        "Count verses per book (aggregate)"
    ))

    conn.close()
    return benchmarks


def benchmark_concordance_queries():
    """Benchmark common queries on concordance.db"""
    if not CONCORDANCE_DB.exists():
        return []

    conn = sqlite3.connect(CONCORDANCE_DB)
    benchmarks = []

    # Query 1: Token lookup
    benchmarks.append(benchmark_query(
        conn,
        "SELECT * FROM tokens WHERE strong_norm LIKE 'G%' LIMIT 100",
        "Fetch 100 Greek tokens"
    ))

    # Query 2: Strong's lexicon lookup
    benchmarks.append(benchmark_query(
        conn,
        "SELECT * FROM strongs_lexicon WHERE strong_norm = 'G2424'",
        "Lookup specific Strong's number"
    ))

    # Query 3: Verse full-text search
    benchmarks.append(benchmark_query(
        conn,
        "SELECT * FROM verses_fts WHERE text MATCH 'love' LIMIT 50",
        "Full-text search for 'love'"
    ))

    # Query 4: Join tokens with lexicon
    benchmarks.append(benchmark_query(
        conn,
        """
        SELECT t.text, l.definition
        FROM tokens t
        LEFT JOIN strongs_lexicon l ON t.strong_norm = l.strong_norm
        LIMIT 500
        """,
        "Join tokens with Strong's lexicon (500 rows)"
    ))

    conn.close()
    return benchmarks


def get_table_record_counts():
    """Count records in all major tables"""
    counts = {'goodbook': {}, 'concordance': {}}

    # GoodBook.db
    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        tables = ['books', 'chapters', 'verses', 'cross_references', 'lexical_words', 'verse_words', 'morphology']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                counts['goodbook'][table] = count
            except sqlite3.Error:
                counts['goodbook'][table] = 'N/A'

        conn.close()

    # concordance.db
    if CONCORDANCE_DB.exists():
        conn = sqlite3.connect(CONCORDANCE_DB)
        cursor = conn.cursor()

        tables = ['books', 'chapters', 'verses', 'tokens', 'strongs_lexicon', 'footnotes']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                counts['concordance'][table] = count
            except sqlite3.Error:
                counts['concordance'][table] = 'N/A'

        conn.close()

    return counts


def check_index_effectiveness():
    """Check which indexes exist and their effectiveness"""
    indexes = {'goodbook': [], 'concordance': []}

    # GoodBook.db
    if GOODBOOK_DB.exists():
        conn = sqlite3.connect(GOODBOOK_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
        for name, table in cursor.fetchall():
            indexes['goodbook'].append({
                'name': name,
                'table': table
            })

        conn.close()

    # concordance.db
    if CONCORDANCE_DB.exists():
        conn = sqlite3.connect(CONCORDANCE_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
        for name, table in cursor.fetchall():
            indexes['concordance'].append({
                'name': name,
                'table': table
            })

        conn.close()

    return indexes


def suggest_optimizations(benchmarks):
    """Suggest optimizations based on benchmark results"""
    suggestions = []

    for benchmark in benchmarks:
        avg_time = benchmark['average_ms']

        if avg_time > 1000:  # Slower than 1 second
            suggestions.append({
                'query': benchmark['description'],
                'issue': f'Slow query ({avg_time:.1f}ms)',
                'severity': 'high',
                'recommendation': 'Consider adding indexes or optimizing the query'
            })
        elif avg_time > 500:  # Slower than 500ms
            suggestions.append({
                'query': benchmark['description'],
                'issue': f'Moderate query time ({avg_time:.1f}ms)',
                'severity': 'medium',
                'recommendation': 'May benefit from indexing or query optimization'
            })

    return suggestions


def main():
    """Main analysis function"""
    print("Starting Performance Benchmarks Analysis...")
    print(f"Output will be saved to: {OUTPUT_FILE}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get database sizes
    print("\n1. Measuring database file sizes...")
    goodbook_size = get_database_size(GOODBOOK_DB)
    concordance_size = get_database_size(CONCORDANCE_DB)

    if goodbook_size:
        print(f"   -> GoodBook.db: {goodbook_size['human_readable']}")
    if concordance_size:
        print(f"   -> concordance.db: {concordance_size['human_readable']}")

    # Benchmark queries
    print("\n2. Benchmarking GoodBook.db queries...")
    goodbook_benchmarks = benchmark_goodbook_queries()
    if goodbook_benchmarks:
        avg_goodbook = sum(b['average_ms'] for b in goodbook_benchmarks) / len(goodbook_benchmarks)
        print(f"   -> Completed {len(goodbook_benchmarks)} benchmarks (avg: {avg_goodbook:.2f}ms)")

    print("\n3. Benchmarking concordance.db queries...")
    concordance_benchmarks = benchmark_concordance_queries()
    if concordance_benchmarks:
        avg_concordance = sum(b['average_ms'] for b in concordance_benchmarks) / len(concordance_benchmarks)
        print(f"   -> Completed {len(concordance_benchmarks)} benchmarks (avg: {avg_concordance:.2f}ms)")

    # Get record counts
    print("\n4. Counting records in all tables...")
    record_counts = get_table_record_counts()
    total_records = sum(v for v in record_counts['goodbook'].values() if isinstance(v, int))
    total_records += sum(v for v in record_counts['concordance'].values() if isinstance(v, int))
    print(f"   -> Total records across all tables: {total_records:,}")

    # Check indexes
    print("\n5. Analyzing database indexes...")
    indexes = check_index_effectiveness()
    total_indexes = len(indexes['goodbook']) + len(indexes['concordance'])
    print(f"   -> Found {total_indexes} indexes across both databases")

    # Generate optimization suggestions
    print("\n6. Generating optimization recommendations...")
    all_benchmarks = goodbook_benchmarks + concordance_benchmarks
    optimizations = suggest_optimizations(all_benchmarks)
    print(f"   -> Generated {len(optimizations)} optimization suggestions")

    # Compile results
    results = {
        'metadata': {
            'analysis_date': datetime.now().isoformat(),
            'databases_analyzed': {
                'goodbook_db': str(GOODBOOK_DB),
                'concordance_db': str(CONCORDANCE_DB)
            }
        },
        'database_sizes': {
            'goodbook': goodbook_size,
            'concordance': concordance_size
        },
        'query_benchmarks': {
            'goodbook': goodbook_benchmarks,
            'concordance': concordance_benchmarks
        },
        'record_counts': record_counts,
        'indexes': indexes,
        'optimization_suggestions': optimizations,
        'performance_summary': {
            'total_benchmarks': len(all_benchmarks),
            'average_query_time_ms': round(sum(b['average_ms'] for b in all_benchmarks) / len(all_benchmarks), 2) if all_benchmarks else 0,
            'slowest_query': max(all_benchmarks, key=lambda x: x['average_ms']) if all_benchmarks else None,
            'fastest_query': min(all_benchmarks, key=lambda x: x['average_ms']) if all_benchmarks else None
        }
    }

    # Save to JSON
    print(f"\n7. Saving results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n[DONE] Performance Benchmarks Analysis Complete!")
    print(f"  Average query time: {results['performance_summary']['average_query_time_ms']}ms")
    print(f"  Output: {OUTPUT_FILE}")

    return results


if __name__ == "__main__":
    main()
