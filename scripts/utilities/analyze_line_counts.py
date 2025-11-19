#!/usr/bin/env python3
"""
Analyze line counts for all text files in a directory
"""

from pathlib import Path
import statistics

def analyze_line_counts(directory_path):
    """
    Analyze line counts for all .txt files in a directory

    Args:
        directory_path: Path to directory containing text files

    Returns:
        Dictionary with analysis results
    """

    directory = Path(directory_path)
    all_files = list(directory.glob('*.txt'))

    if not all_files:
        print(f"No .txt files found in {directory}")
        return None

    file_stats = []

    for file_path in all_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            line_count = text.count('\n') + 1
            char_count = len(text)
            word_count = len(text.split())

            file_stats.append({
                'name': file_path.name,
                'path': file_path,
                'lines': line_count,
                'chars': char_count,
                'words': word_count,
                'avg_chars_per_line': char_count / line_count if line_count > 0 else 0,
                'avg_words_per_line': word_count / line_count if line_count > 0 else 0
            })
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    return file_stats

def print_analysis(file_stats, directory_path):
    """Print comprehensive analysis of line counts"""

    if not file_stats:
        return

    # Calculate statistics
    line_counts = [f['lines'] for f in file_stats]
    char_counts = [f['chars'] for f in file_stats]
    word_counts = [f['words'] for f in file_stats]

    total_files = len(file_stats)
    total_lines = sum(line_counts)
    total_chars = sum(char_counts)
    total_words = sum(word_counts)

    mean_lines = statistics.mean(line_counts)
    median_lines = statistics.median(line_counts)
    stdev_lines = statistics.stdev(line_counts) if len(line_counts) > 1 else 0
    min_lines = min(line_counts)
    max_lines = max(line_counts)

    # Categorize files
    categories = {
        '1-10 lines': [f for f in file_stats if f['lines'] <= 10],
        '11-25 lines': [f for f in file_stats if 11 <= f['lines'] <= 25],
        '26-50 lines': [f for f in file_stats if 26 <= f['lines'] <= 50],
        '51-100 lines': [f for f in file_stats if 51 <= f['lines'] <= 100],
        '101-200 lines': [f for f in file_stats if 101 <= f['lines'] <= 200],
        '201+ lines': [f for f in file_stats if f['lines'] > 200]
    }

    # Print report
    print("=" * 100)
    print("LINE COUNT ANALYSIS")
    print("=" * 100)
    print(f"\nDirectory: {directory_path}")
    print(f"Total files analyzed: {total_files:,}")
    print()

    print("OVERALL STATISTICS:")
    print("-" * 100)
    print(f"  Total lines:        {total_lines:>12,}")
    print(f"  Total characters:   {total_chars:>12,}")
    print(f"  Total words:        {total_words:>12,}")
    print()
    print(f"  Mean lines/file:    {mean_lines:>12,.1f}")
    print(f"  Median lines/file:  {median_lines:>12,.1f}")
    print(f"  Std dev:            {stdev_lines:>12,.1f}")
    print(f"  Min lines:          {min_lines:>12,}")
    print(f"  Max lines:          {max_lines:>12,}")
    print()
    print(f"  Avg chars/file:     {total_chars/total_files:>12,.0f}")
    print(f"  Avg words/file:     {total_words/total_files:>12,.0f}")
    print()

    print("DISTRIBUTION BY LINE COUNT:")
    print("-" * 100)
    for category, files in categories.items():
        count = len(files)
        percentage = (count / total_files * 100) if total_files > 0 else 0
        bar_length = int(percentage / 2)  # Scale to 50 chars max
        bar = '#' * bar_length
        print(f"  {category:15} {count:>5} ({percentage:>5.1f}%)  {bar}")
    print()

    # Show smallest and largest files
    sorted_by_lines = sorted(file_stats, key=lambda x: x['lines'])

    print("SMALLEST FILES (by line count):")
    print("-" * 100)
    for i, f in enumerate(sorted_by_lines[:10], 1):
        print(f"  {i:2}. {f['lines']:>4} lines | {f['words']:>6,} words | {f['name'][:60]}")
    print()

    print("LARGEST FILES (by line count):")
    print("-" * 100)
    for i, f in enumerate(sorted_by_lines[-10:][::-1], 1):
        print(f"  {i:2}. {f['lines']:>4} lines | {f['words']:>6,} words | {f['name'][:60]}")
    print()

    # Percentile analysis
    print("PERCENTILE ANALYSIS:")
    print("-" * 100)
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    for p in percentiles:
        value = statistics.quantiles(line_counts, n=100)[p-1] if len(line_counts) > 1 else line_counts[0]
        print(f"  {p:>2}th percentile: {value:>6.1f} lines")
    print()

    # Files that might need attention (< 11 lines)
    short_files = [f for f in file_stats if f['lines'] <= 10]
    if short_files:
        print(f"FILES WITH 10 OR FEWER LINES ({len(short_files)}):")
        print("-" * 100)
        for i, f in enumerate(sorted(short_files, key=lambda x: x['lines']), 1):
            print(f"  {i:2}. {f['lines']:>3} lines | {f['chars']:>7,} chars | {f['name']}")
    else:
        print("✓ No files with 10 or fewer lines found!")

    print()
    print("=" * 100)

def main():
    """Main function"""

    # Default directory
    default_dir = r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts_cleaned'

    # You can change this path or pass as command line argument
    import sys
    directory_path = sys.argv[1] if len(sys.argv) > 1 else default_dir

    print(f"Analyzing text files in: {directory_path}\n")

    # Analyze files
    file_stats = analyze_line_counts(directory_path)

    if file_stats:
        # Print analysis
        print_analysis(file_stats, directory_path)

        # Optionally save to CSV
        save_csv = input("\nSave detailed results to CSV? (y/n): ").lower().strip()
        if save_csv == 'y':
            import csv
            output_file = Path(directory_path) / 'line_count_analysis.csv'

            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'lines', 'chars', 'words', 'avg_chars_per_line', 'avg_words_per_line']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for f in sorted(file_stats, key=lambda x: x['lines'], reverse=True):
                    writer.writerow({
                        'name': f['name'],
                        'lines': f['lines'],
                        'chars': f['chars'],
                        'words': f['words'],
                        'avg_chars_per_line': f['avg_chars_per_line'],
                        'avg_words_per_line': f['avg_words_per_line']
                    })

            print(f"\nDetailed results saved to: {output_file}")

if __name__ == '__main__':
    main()
