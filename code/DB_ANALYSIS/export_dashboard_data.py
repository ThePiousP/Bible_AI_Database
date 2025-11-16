#!/usr/bin/env python3
"""
Dashboard Data Exporter
Combines all analysis JSON files into a single dashboard_data.json for HTML visualization
"""

import json
from pathlib import Path
from datetime import datetime


# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "Analytics"
OUTPUT_FILE = OUTPUT_DIR / "dashboard_data.json"


def load_all_analyses():
    """Load all analysis JSON files"""
    analyses = {}

    files = {
        'content_distribution': 'content_distribution.json',
        'theology_coverage': 'theology_coverage.json',
        'crossref_network': 'crossref_network.json',
        'difficulty_profile': 'difficulty_profile.json',
        'clue_quality': 'clue_quality.json',
        'completeness_report': 'completeness_report.json',
        'performance_metrics': 'performance_metrics.json',
        'executive_summary': 'executive_summary.json'
    }

    for key, filename in files.items():
        filepath = OUTPUT_DIR / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                analyses[key] = json.load(f)
        else:
            print(f"   Warning: {filename} not found - skipping")
            analyses[key] = None

    return analyses


def prepare_chart_data(analyses):
    """Prepare data specifically formatted for Chart.js visualizations"""
    chart_data = {}

    # 1. Word Length Distribution (Bar Chart)
    if analyses['content_distribution']:
        length_dist = analyses['content_distribution'].get('word_length_distribution', {}).get('distribution', {})
        chart_data['word_length_distribution'] = {
            'labels': [str(k) for k in sorted(length_dist.keys(), key=int)],
            'values': [length_dist[k] for k in sorted(length_dist.keys(), key=int)],
            'type': 'bar',
            'title': 'Word Length Distribution'
        }

        # 2. Letter Frequency (Bar Chart)
        letter_freq = analyses['content_distribution'].get('letter_frequency', {}).get('frequencies', {})
        chart_data['letter_frequency'] = {
            'labels': list(letter_freq.keys()),
            'values': [letter_freq[k]['count'] for k in letter_freq.keys()],
            'type': 'bar',
            'title': 'Letter Frequency Distribution'
        }

    # 3. Testament Balance (Pie Chart)
    if analyses['theology_coverage']:
        testament = analyses['theology_coverage'].get('testament_balance', {})
        chart_data['testament_balance'] = {
            'labels': ['Old Testament', 'New Testament'],
            'values': [
                testament.get('old_testament', {}).get('verses', 0),
                testament.get('new_testament', {}).get('verses', 0)
            ],
            'type': 'pie',
            'title': 'Old Testament vs New Testament (Verses)'
        }

    # 4. Strong's Coverage (Progress Bars)
    if analyses['theology_coverage']:
        strongs = analyses['theology_coverage'].get('strongs_coverage', {})
        chart_data['strongs_coverage'] = {
            'hebrew': strongs.get('hebrew', {}).get('coverage_percentage', 0),
            'greek': strongs.get('greek', {}).get('coverage_percentage', 0),
            'type': 'progress',
            'title': "Strong's Number Coverage"
        }

    # 5. Clue Distribution (Bar Chart)
    if analyses['clue_quality']:
        clue_dist = analyses['clue_quality'].get('coverage', {}).get('distribution', {})
        chart_data['clue_distribution'] = {
            'labels': ['0 Clues', '1 Clue', '2 Clues', '3 Clues', '4+ Clues'],
            'values': [
                clue_dist.get('words_with_0_clues', 0),
                clue_dist.get('words_with_1_clue', 0),
                clue_dist.get('words_with_2_clues', 0),
                clue_dist.get('words_with_3_clues', 0),
                clue_dist.get('words_with_4plus_clues', 0)
            ],
            'type': 'bar',
            'title': 'Clues per Word Distribution'
        }

    # 6. Difficulty Distribution (Pie Chart)
    if analyses['difficulty_profile']:
        word_class = analyses['difficulty_profile'].get('word_frequency_classification', {})
        chart_data['difficulty_distribution'] = {
            'labels': ['Common Words', 'Uncommon Words', 'Rare Words'],
            'values': [
                word_class.get('common', {}).get('count', 0),
                word_class.get('uncommon', {}).get('count', 0),
                word_class.get('rare', {}).get('count', 0)
            ],
            'type': 'pie',
            'title': 'Word Difficulty Distribution'
        }

    # 7. Connection Distribution (Bar Chart - top 10 connection counts)
    if analyses['crossref_network'] and analyses['crossref_network'].get('connection_distribution'):
        conn_dist = analyses['crossref_network'].get('connection_distribution', {})
        # Sort and take top 10
        sorted_connections = sorted(conn_dist.items(), key=lambda x: int(x[0]))[:10]
        chart_data['connection_distribution'] = {
            'labels': [f"{k} connections" for k, v in sorted_connections],
            'values': [v for k, v in sorted_connections],
            'type': 'bar',
            'title': 'Cross-Reference Connection Distribution'
        }

    return chart_data


def prepare_summary_stats(analyses):
    """Prepare key summary statistics for dashboard cards"""
    stats = {}

    # Executive Summary Stats
    if analyses['executive_summary']:
        stats['confidence_score'] = analyses['executive_summary'].get('confidence_score', {}).get('overall', 0)
        stats['ai_readiness'] = analyses['executive_summary'].get('ai_readiness', {}).get('readiness', 'Unknown')

    # Content Stats
    if analyses['content_distribution']:
        stats['total_unique_words'] = analyses['content_distribution'].get('metadata', {}).get('total_unique_words', 0)
        stats['average_word_length'] = analyses['content_distribution'].get('word_length_distribution', {}).get('average_length', 0)

    # Theology Stats
    if analyses['theology_coverage']:
        stats['hebrew_coverage'] = analyses['theology_coverage'].get('strongs_coverage', {}).get('hebrew', {}).get('coverage_percentage', 0)
        stats['greek_coverage'] = analyses['theology_coverage'].get('strongs_coverage', {}).get('greek', {}).get('coverage_percentage', 0)

    # Cross-Reference Stats
    if analyses['crossref_network'] and 'summary' in analyses['crossref_network']:
        stats['total_cross_references'] = analyses['crossref_network'].get('summary', {}).get('total_cross_references', 0)
        stats['avg_connections_per_verse'] = analyses['crossref_network'].get('summary', {}).get('average_connections_per_verse', 0)

    # Clue Stats
    if analyses['clue_quality']:
        stats['clue_coverage'] = analyses['clue_quality'].get('coverage', {}).get('coverage_percentage', 0)
        stats['average_clues_per_word'] = analyses['clue_quality'].get('coverage', {}).get('average_clues_per_word', 0)

    # Performance Stats
    if analyses['performance_metrics']:
        stats['average_query_time_ms'] = analyses['performance_metrics'].get('performance_summary', {}).get('average_query_time_ms', 0)

    # Completeness Stats
    if analyses['completeness_report']:
        stats['health_score'] = analyses['completeness_report'].get('health_score', 0)
        stats['health_status'] = analyses['completeness_report'].get('health_status', 'Unknown')

    return stats


def prepare_tables_data(analyses):
    """Prepare data for HTML tables"""
    tables = {}

    # Most Connected Verses Table
    if analyses['crossref_network'] and analyses['crossref_network'].get('most_connected_verses'):
        tables['most_connected_verses'] = analyses['crossref_network']['most_connected_verses'][:20]

    # Underrepresented Books Table
    if analyses['completeness_report']:
        tables['underrepresented_books'] = analyses['completeness_report'].get('underrepresented_books', [])

    # Top Theological Concepts
    if analyses['theology_coverage']:
        concepts = analyses['theology_coverage'].get('theological_concepts', {}).get('most_frequent', [])
        tables['theological_concepts'] = [
            {'concept': concept, 'count': count}
            for concept, count in concepts
        ]

    # Performance Benchmarks Table
    if analyses['performance_metrics']:
        goodbook_bench = analyses['performance_metrics'].get('query_benchmarks', {}).get('goodbook', [])
        concordance_bench = analyses['performance_metrics'].get('query_benchmarks', {}).get('concordance', [])
        tables['performance_benchmarks'] = goodbook_bench + concordance_bench

    return tables


def main():
    """Main export function"""
    print("Exporting Dashboard Data...")
    print(f"Output will be saved to: {OUTPUT_FILE}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load all analyses
    print("\n1. Loading all analysis files...")
    analyses = load_all_analyses()
    loaded_count = sum(1 for v in analyses.values() if v is not None)
    print(f"   -> Loaded {loaded_count}/8 analysis files")

    # Prepare chart data
    print("\n2. Preparing chart data for visualizations...")
    chart_data = prepare_chart_data(analyses)
    print(f"   -> Prepared {len(chart_data)} charts")

    # Prepare summary statistics
    print("\n3. Preparing summary statistics...")
    summary_stats = prepare_summary_stats(analyses)
    print(f"   -> Prepared {len(summary_stats)} statistics")

    # Prepare table data
    print("\n4. Preparing table data...")
    tables = prepare_tables_data(analyses)
    print(f"   -> Prepared {len(tables)} tables")

    # Compile dashboard data
    dashboard_data = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'version': '1.0',
            'analyses_included': loaded_count,
            'total_analyses': 8
        },
        'summary_stats': summary_stats,
        'charts': chart_data,
        'tables': tables,
        'raw_analyses': {
            'executive_summary': analyses['executive_summary'],
            'content_distribution': analyses['content_distribution'],
            'theology_coverage': analyses['theology_coverage'],
            'crossref_network': analyses['crossref_network'],
            'difficulty_profile': analyses['difficulty_profile'],
            'clue_quality': analyses['clue_quality'],
            'completeness_report': analyses['completeness_report'],
            'performance_metrics': analyses['performance_metrics']
        }
    }

    # Save to JSON
    print(f"\n5. Saving dashboard data to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)

    print("\n[DONE] Dashboard Data Export Complete!")
    print(f"  Output: {OUTPUT_FILE}")
    print(f"\n  You can now open the HTML dashboard to visualize this data.")

    return dashboard_data


if __name__ == "__main__":
    main()
