#!/usr/bin/env python3
"""
Executive Report Generator
Aggregates all analysis results and generates an executive summary with confidence score
"""

import json
from pathlib import Path
from datetime import datetime


# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "Analytics"
OUTPUT_FILE = OUTPUT_DIR / "executive_summary.json"


def load_analysis_results():
    """Load all analysis JSON files"""
    results = {}

    analysis_files = {
        'content': OUTPUT_DIR / 'content_distribution.json',
        'theology': OUTPUT_DIR / 'theology_coverage.json',
        'crossrefs': OUTPUT_DIR / 'crossref_network.json',
        'difficulty': OUTPUT_DIR / 'difficulty_profile.json',
        'clues': OUTPUT_DIR / 'clue_quality.json',
        'completeness': OUTPUT_DIR / 'completeness_report.json',
        'performance': OUTPUT_DIR / 'performance_metrics.json'
    }

    for key, filepath in analysis_files.items():
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                results[key] = json.load(f)
        else:
            print(f"   Warning: {filepath.name} not found")
            results[key] = None

    return results


def calculate_confidence_score(results):
    """Calculate overall confidence score (0-100) based on all analyses"""
    scores = {}
    weights = {}

    # 1. Content Distribution Score (10% weight)
    if results['content']:
        content_score = 100  # Base score
        total_words = results['content'].get('metadata', {}).get('total_unique_words', 0)
        if total_words < 1000:
            content_score -= 40
        elif total_words < 5000:
            content_score -= 20
        scores['content'] = content_score
        weights['content'] = 10

    # 2. Theological Coverage Score (25% weight)
    if results['theology']:
        theology_score = 100
        strongs = results['theology'].get('strongs_coverage', {})

        # Hebrew coverage
        hebrew_pct = strongs.get('hebrew', {}).get('coverage_percentage', 0)
        if hebrew_pct < 50:
            theology_score -= 30
        elif hebrew_pct < 75:
            theology_score -= 15

        # Greek coverage
        greek_pct = strongs.get('greek', {}).get('coverage_percentage', 0)
        if greek_pct < 50:
            theology_score -= 30
        elif greek_pct < 75:
            theology_score -= 15

        scores['theology'] = max(0, theology_score)
        weights['theology'] = 25

    # 3. Cross-Reference Network Score (15% weight)
    if results['crossrefs'] and 'summary' in results['crossrefs']:
        xref_score = 100
        total_xrefs = results['crossrefs'].get('summary', {}).get('total_cross_references', 0)
        avg_connections = results['crossrefs'].get('summary', {}).get('average_connections_per_verse', 0)

        if total_xrefs < 1000:
            xref_score -= 40
        elif total_xrefs < 5000:
            xref_score -= 20

        if avg_connections < 1:
            xref_score -= 20

        scores['crossrefs'] = max(0, xref_score)
        weights['crossrefs'] = 15

    # 4. Difficulty/Accessibility Score (10% weight)
    if results['difficulty']:
        diff_score = 80  # Slightly lower base (complexity is expected)
        scores['difficulty'] = diff_score
        weights['difficulty'] = 10

    # 5. Clue Quality Score (20% weight)
    if results['clues']:
        clue_score = 100
        coverage = results['clues'].get('coverage', {})
        coverage_pct = coverage.get('coverage_percentage', 0)
        avg_clues = coverage.get('average_clues_per_word', 0)

        if coverage_pct < 50:
            clue_score -= 50
        elif coverage_pct < 75:
            clue_score -= 30
        elif coverage_pct < 90:
            clue_score -= 15

        if avg_clues < 1:
            clue_score -= 20
        elif avg_clues < 2:
            clue_score -= 10

        scores['clues'] = max(0, clue_score)
        weights['clues'] = 20

    # 6. Completeness Score (15% weight)
    if results['completeness']:
        completeness_score = results['completeness'].get('health_score', 50)
        scores['completeness'] = completeness_score
        weights['completeness'] = 15

    # 7. Performance Score (5% weight)
    if results['performance']:
        perf_score = 100
        avg_query_time = results['performance'].get('performance_summary', {}).get('average_query_time_ms', 0)

        if avg_query_time > 500:
            perf_score -= 40
        elif avg_query_time > 100:
            perf_score -= 20

        scores['performance'] = max(0, perf_score)
        weights['performance'] = 5

    # Calculate weighted average
    if not scores:
        return 0, {}, {}

    total_weight = sum(weights.values())
    weighted_score = sum(scores[k] * weights[k] for k in scores.keys()) / total_weight if total_weight > 0 else 0

    return round(weighted_score, 1), scores, weights


def identify_strengths(results, scores):
    """Identify top 5 strengths of the database"""
    strengths = []

    # Check each category
    if scores.get('content', 0) >= 90:
        strengths.append({
            'category': 'Content Distribution',
            'score': scores['content'],
            'description': f"Excellent word coverage with {results['content'].get('metadata', {}).get('total_unique_words', 0):,} unique words"
        })

    if scores.get('theology', 0) >= 85:
        hebrew_pct = results['theology'].get('strongs_coverage', {}).get('hebrew', {}).get('coverage_percentage', 0)
        greek_pct = results['theology'].get('strongs_coverage', {}).get('greek', {}).get('coverage_percentage', 0)
        strengths.append({
            'category': 'Theological Coverage',
            'score': scores['theology'],
            'description': f"Strong Strong's coverage: Hebrew {hebrew_pct}%, Greek {greek_pct}%"
        })

    if scores.get('crossrefs', 0) >= 85:
        total_xrefs = results['crossrefs'].get('summary', {}).get('total_cross_references', 0) if results['crossrefs'] and 'summary' in results['crossrefs'] else 0
        strengths.append({
            'category': 'Cross-References',
            'score': scores['crossrefs'],
            'description': f"Comprehensive cross-reference network with {total_xrefs:,} connections"
        })

    if scores.get('clues', 0) >= 85:
        coverage_pct = results['clues'].get('coverage', {}).get('coverage_percentage', 0)
        strengths.append({
            'category': 'Clue Quality',
            'score': scores['clues'],
            'description': f"High clue coverage at {coverage_pct}%"
        })

    if scores.get('completeness', 0) >= 85:
        health_status = results['completeness'].get('health_status', 'Unknown')
        strengths.append({
            'category': 'Data Completeness',
            'score': scores['completeness'],
            'description': f"Database health status: {health_status}"
        })

    if scores.get('performance', 0) >= 90:
        avg_time = results['performance'].get('performance_summary', {}).get('average_query_time_ms', 0)
        strengths.append({
            'category': 'Query Performance',
            'score': scores['performance'],
            'description': f"Excellent query performance: {avg_time:.1f}ms average"
        })

    # Sort by score and return top 5
    return sorted(strengths, key=lambda x: x['score'], reverse=True)[:5]


def identify_gaps(results, scores):
    """Identify top 5 gaps/weaknesses that need attention"""
    gaps = []

    # Check each category for issues
    if scores.get('content', 100) < 80:
        gaps.append({
            'category': 'Content Distribution',
            'score': scores.get('content', 0),
            'description': 'Limited word coverage - consider expanding vocabulary',
            'priority': 'high' if scores.get('content', 0) < 50 else 'medium'
        })

    if scores.get('theology', 100) < 80:
        hebrew_gaps = results['theology'].get('strongs_coverage', {}).get('hebrew', {}).get('gaps_count', 0) if results['theology'] else 0
        greek_gaps = results['theology'].get('strongs_coverage', {}).get('greek', {}).get('gaps_count', 0) if results['theology'] else 0
        gaps.append({
            'category': 'Theological Coverage',
            'score': scores.get('theology', 0),
            'description': f"Strong's gaps: {hebrew_gaps} Hebrew, {greek_gaps} Greek numbers missing",
            'priority': 'high'
        })

    if scores.get('crossrefs', 100) < 80:
        gaps.append({
            'category': 'Cross-References',
            'score': scores.get('crossrefs', 0),
            'description': 'Limited cross-reference network - expand verse connections',
            'priority': 'medium'
        })

    if scores.get('clues', 100) < 80:
        words_no_clues = results['clues'].get('coverage', {}).get('distribution', {}).get('words_with_0_clues', 0) if results['clues'] else 0
        gaps.append({
            'category': 'Clue Quality',
            'score': scores.get('clues', 0),
            'description': f"{words_no_clues:,} words have no clues - requires clue generation",
            'priority': 'high'
        })

    if scores.get('completeness', 100) < 80:
        total_issues = results['completeness'].get('total_issues_found', 0) if results['completeness'] else 0
        gaps.append({
            'category': 'Data Completeness',
            'score': scores.get('completeness', 0),
            'description': f"{total_issues} data integrity issues found - requires cleanup",
            'priority': 'high' if total_issues > 10 else 'medium'
        })

    if scores.get('performance', 100) < 70:
        gaps.append({
            'category': 'Query Performance',
            'score': scores.get('performance', 0),
            'description': 'Slow query performance - consider adding indexes or optimizing',
            'priority': 'medium'
        })

    # Sort by priority (high first) and score (low first)
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    return sorted(gaps, key=lambda x: (priority_order.get(x['priority'], 3), x['score']))[:5]


def determine_ai_readiness(confidence_score, strengths, gaps):
    """Determine if database is ready for AI/NLP development"""
    if confidence_score >= 90:
        readiness = 'READY'
        status_color = 'green'
        recommendation = 'Database is excellent for AI/NLP development. All critical metrics are strong.'
    elif confidence_score >= 75:
        readiness = 'READY WITH MINOR IMPROVEMENTS'
        status_color = 'yellow'
        recommendation = 'Database is good for AI development. Address minor gaps for optimal results.'
    elif confidence_score >= 60:
        readiness = 'NEEDS IMPROVEMENT'
        status_color = 'orange'
        recommendation = 'Database has potential but requires significant improvements before AI development.'
    else:
        readiness = 'NOT READY'
        status_color = 'red'
        recommendation = 'Database needs substantial work. Focus on addressing critical gaps first.'

    return {
        'readiness': readiness,
        'status_color': status_color,
        'recommendation': recommendation,
        'critical_actions': [gap['description'] for gap in gaps if gap.get('priority') == 'high'][:3]
    }


def main():
    """Main report generation function"""
    print("Generating Executive Summary Report...")
    print(f"Output will be saved to: {OUTPUT_FILE}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load all analysis results
    print("\n1. Loading analysis results...")
    results = load_analysis_results()
    analyses_loaded = sum(1 for v in results.values() if v is not None)
    print(f"   -> Loaded {analyses_loaded}/7 analysis files")

    # Calculate confidence score
    print("\n2. Calculating confidence score...")
    confidence_score, category_scores, weights = calculate_confidence_score(results)
    print(f"   -> Overall confidence: {confidence_score}/100")

    # Identify strengths
    print("\n3. Identifying strengths...")
    strengths = identify_strengths(results, category_scores)
    print(f"   -> Found {len(strengths)} major strengths")

    # Identify gaps
    print("\n4. Identifying gaps and weaknesses...")
    gaps = identify_gaps(results, category_scores)
    print(f"   -> Found {len(gaps)} areas needing improvement")

    # Determine AI readiness
    print("\n5. Assessing AI development readiness...")
    ai_readiness = determine_ai_readiness(confidence_score, strengths, gaps)
    print(f"   -> Readiness status: {ai_readiness['readiness']}")

    # Compile executive summary
    summary = {
        'metadata': {
            'report_generated': datetime.now().isoformat(),
            'analyses_included': analyses_loaded,
            'total_analyses': 7
        },
        'confidence_score': {
            'overall': confidence_score,
            'category_scores': category_scores,
            'weights': weights
        },
        'strengths': strengths,
        'gaps': gaps,
        'ai_readiness': ai_readiness,
        'detailed_results': {
            'content_distribution': results['content'] is not None,
            'theological_coverage': results['theology'] is not None,
            'cross_references': results['crossrefs'] is not None,
            'difficulty_profile': results['difficulty'] is not None,
            'clue_quality': results['clues'] is not None,
            'completeness': results['completeness'] is not None,
            'performance': results['performance'] is not None
        }
    }

    # Save to JSON
    print(f"\n6. Saving executive summary to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print("EXECUTIVE SUMMARY")
    print("="*70)
    print(f"\nOverall Confidence Score: {confidence_score}/100")
    print(f"AI Readiness: {ai_readiness['readiness']}")
    print(f"\n{ai_readiness['recommendation']}")

    if strengths:
        print(f"\n[DONE] Top Strengths:")
        for s in strengths:
            print(f"  • {s['category']}: {s['description']}")

    if gaps:
        print(f"\n[WARNING] Areas Needing Improvement:")
        for g in gaps:
            priority_marker = "[HIGH]" if g.get('priority') == 'high' else "[MED]"
            print(f"  {priority_marker} {g['category']}: {g['description']}")

    print(f"\n{'='*70}\n")
    print(f"[DONE] Executive Summary Report Complete!")
    print(f"  Output: {OUTPUT_FILE}")

    return summary


if __name__ == "__main__":
    main()
