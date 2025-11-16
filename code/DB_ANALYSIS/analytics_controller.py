#!/usr/bin/env python3
"""
Bible Database Analytics Controller
Main entry point for running database analytics with menu-driven interface
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Ensure paths are absolute and within project directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
OUTPUT_DIR = PROJECT_ROOT / "output" / "Analytics"
CODE_DIR = PROJECT_ROOT / "code" / "DB_ANALYSIS"

# Add the code directory to Python path
sys.path.insert(0, str(CODE_DIR))

# Security check: Ensure output directory is within project
if not str(OUTPUT_DIR).startswith(str(PROJECT_ROOT)):
    print(f"ERROR: Output directory {OUTPUT_DIR} is outside project root {PROJECT_ROOT}")
    print("This is a security violation. Aborting.")
    sys.exit(1)

# Import analysis modules (will be created)
ANALYSIS_MODULES = {
    '1': {
        'name': 'Content Distribution Analysis',
        'module': 'analyze_content',
        'output': 'content_distribution.json',
        'description': 'Word length, letter frequency, bigrams, rare combinations'
    },
    '2': {
        'name': 'Theological Coverage Analysis',
        'module': 'analyze_theology',
        'output': 'theology_coverage.json',
        'description': 'Book distribution, OT/NT balance, Strong\'s coverage, entity types'
    },
    '3': {
        'name': 'Cross-Reference Network Analysis',
        'module': 'analyze_crossrefs',
        'output': 'crossref_network.json',
        'description': 'Network metrics, most-connected verses, isolated verses, hubs'
    },
    '4': {
        'name': 'Difficulty Profile Analysis',
        'module': 'analyze_difficulty',
        'output': 'difficulty_profile.json',
        'description': 'Word frequency, reading level, Greek/Hebrew terms, accessibility'
    },
    '5': {
        'name': 'Clue Quality Assessment',
        'module': 'analyze_clues',
        'output': 'clue_quality.json',
        'description': 'Clue coverage, distribution, uniqueness, quality metrics'
    },
    '6': {
        'name': 'Completeness & Gap Analysis',
        'module': 'analyze_completeness',
        'output': 'completeness_report.json',
        'description': 'Missing data, gaps, duplicates, consistency checks'
    },
    '7': {
        'name': 'Performance Benchmarks',
        'module': 'analyze_performance',
        'output': 'performance_metrics.json',
        'description': 'Query times, database size, optimization opportunities'
    }
}


def print_header():
    """Print the application header"""
    print("\n" + "=" * 70)
    print(" " * 15 + "BIBLE DATABASE ANALYTICS SUITE")
    print("=" * 70)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("=" * 70 + "\n")


def print_menu():
    """Print the main menu"""
    print("\nAVAILABLE ANALYSES:")
    print("-" * 70)
    for key, module in ANALYSIS_MODULES.items():
        print(f"  [{key}] {module['name']}")
        print(f"      -> {module['description']}")
        print()
    print(f"  [A] Run ALL analyses (Full Suite)")
    print(f"  [R] Generate Executive Report (after running analyses)")
    print(f"  [D] Export Dashboard Data (after running analyses)")
    print(f"  [Q] Quit")
    print("-" * 70)


def run_analysis(module_key):
    """Run a specific analysis module"""
    if module_key not in ANALYSIS_MODULES:
        print(f"ERROR: Invalid module key: {module_key}")
        return False

    module_info = ANALYSIS_MODULES[module_key]
    module_name = module_info['module']

    print(f"\n{'='*70}")
    print(f"RUNNING: {module_info['name']}")
    print(f"{'='*70}\n")

    try:
        # Import and run the module
        module = __import__(module_name)
        if hasattr(module, 'main'):
            result = module.main()
            print(f"\n[DONE] Analysis complete: {module_info['output']}")
            return True
        else:
            print(f"ERROR: Module {module_name} has no main() function")
            return False
    except ImportError as e:
        print(f"ERROR: Could not import module '{module_name}': {e}")
        return False
    except Exception as e:
        print(f"ERROR running {module_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_analyses():
    """Run all analysis modules in sequence"""
    print(f"\n{'='*70}")
    print("RUNNING FULL ANALYSIS SUITE")
    print(f"{'='*70}\n")

    results = {}
    start_time = datetime.now()

    for key in sorted(ANALYSIS_MODULES.keys()):
        success = run_analysis(key)
        results[ANALYSIS_MODULES[key]['name']] = success
        print()

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Print summary
    print(f"\n{'='*70}")
    print("ANALYSIS SUITE SUMMARY")
    print(f"{'='*70}")
    print(f"Duration: {duration:.2f} seconds\n")

    successful = sum(1 for v in results.values() if v)
    total = len(results)

    for name, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status}: {name}")

    print(f"\nResults: {successful}/{total} analyses completed successfully")
    print(f"{'='*70}\n")

    return successful == total


def generate_report():
    """Generate executive summary report"""
    print(f"\n{'='*70}")
    print("GENERATING EXECUTIVE REPORT")
    print(f"{'='*70}\n")

    try:
        import generate_report
        if hasattr(generate_report, 'main'):
            generate_report.main()
            print("\n[DONE] Executive report generated successfully")
            return True
        else:
            print("ERROR: generate_report module has no main() function")
            return False
    except ImportError as e:
        print(f"ERROR: Could not import generate_report module: {e}")
        return False
    except Exception as e:
        print(f"ERROR generating report: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_dashboard():
    """Export data for HTML dashboard"""
    print(f"\n{'='*70}")
    print("EXPORTING DASHBOARD DATA")
    print(f"{'='*70}\n")

    try:
        import export_dashboard_data
        if hasattr(export_dashboard_data, 'main'):
            export_dashboard_data.main()
            print("\n[DONE] Dashboard data exported successfully")
            return True
        else:
            print("ERROR: export_dashboard_data module has no main() function")
            return False
    except ImportError as e:
        print(f"ERROR: Could not import export_dashboard_data module: {e}")
        return False
    except Exception as e:
        print(f"ERROR exporting dashboard data: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main controller loop"""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print_header()

    while True:
        print_menu()
        choice = input("\nEnter your choice: ").strip().upper()

        if choice == 'Q':
            print("\nExiting Analytics Controller. Goodbye!\n")
            break

        elif choice == 'A':
            run_all_analyses()

        elif choice == 'R':
            generate_report()

        elif choice == 'D':
            export_dashboard()

        elif choice in ANALYSIS_MODULES:
            run_analysis(choice)

        else:
            print(f"\n[WARNING] Invalid choice: '{choice}'. Please try again.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
