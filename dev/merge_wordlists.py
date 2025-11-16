#!/usr/bin/env python3
"""
Compare and merge two Bible word lists, removing duplicate WORDs.
Keeps entries from both files, preferring first file when duplicates exist.
"""

import sys
from collections import OrderedDict


def load_wordlist(filepath):
    """Load a tab-delimited word list into an OrderedDict keyed by WORD."""
    words = OrderedDict()

    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            parts = line.split('\t')
            if not parts:
                continue

            word = parts[0].strip().upper()

            # Store the full line
            words[word] = line

    return words


def find_duplicates(words1, words2):
    """Find words that appear in both dictionaries."""
    set1 = set(words1.keys())
    set2 = set(words2.keys())

    duplicates = set1.intersection(set2)
    return sorted(duplicates)


def merge_wordlists(file1, file2, output_file):
    """Merge two word lists, removing duplicates."""
    print(f"Loading {file1}...")
    words1 = load_wordlist(file1)
    print(f"  Loaded {len(words1)} words")

    print(f"\nLoading {file2}...")
    words2 = load_wordlist(file2)
    print(f"  Loaded {len(words2)} words")

    # Find duplicates
    print(f"\nFinding duplicates...")
    duplicates = find_duplicates(words1, words2)
    print(f"  Found {len(duplicates)} duplicate words")

    # Show first 20 duplicates
    if duplicates:
        print(f"\n  First 20 duplicates:")
        for i, word in enumerate(duplicates[:20], 1):
            print(f"    {i}. {word}")
        if len(duplicates) > 20:
            print(f"    ... and {len(duplicates) - 20} more")

    # Merge: Keep all from file1, add non-duplicates from file2
    print(f"\nMerging word lists...")
    merged = OrderedDict()

    # Add all from file1
    for word, line in words1.items():
        merged[word] = line

    # Add non-duplicates from file2
    added_from_file2 = 0
    for word, line in words2.items():
        if word not in merged:
            merged[word] = line
            added_from_file2 += 1

    print(f"  Total words in merged list: {len(merged)}")
    print(f"  Words from {file1}: {len(words1)}")
    print(f"  Words added from {file2}: {added_from_file2}")
    print(f"  Duplicates removed: {len(duplicates)}")

    # Write merged list
    print(f"\nWriting merged list to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in merged.values():
            f.write(line + '\n')

    print(f"  Complete! {len(merged)} words written.")

    # Generate duplicate report
    report_file = output_file.replace('.txt', '_duplicates_report.txt')
    print(f"\nWriting duplicate report to {report_file}...")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Duplicate Words Report\n")
        f.write(f"# Total duplicates found: {len(duplicates)}\n\n")
        f.write(f"File 1: {file1}\n")
        f.write(f"File 2: {file2}\n\n")
        f.write("="*80 + "\n\n")

        for i, word in enumerate(duplicates, 1):
            f.write(f"{i}. {word}\n")
            f.write(f"   FROM FILE 1: {words1[word]}\n")
            f.write(f"   FROM FILE 2: {words2[word]}\n")
            f.write("\n")

    print(f"  Complete!")

    return len(words1), len(words2), len(duplicates), len(merged)


def main():
    file1 = r'D:\Project_PP\projects\bible\dev\strongs_cleaned_for_crossword.txt'
    file2 = r'D:\Project_PP\projects\bible\dev\Complete_bible_list.txt'
    output_file = r'D:\Project_PP\projects\bible\dev\strong_bible_list_v1.txt'

    print("="*80)
    print("BIBLE WORDLIST MERGER")
    print("="*80)
    print()

    count1, count2, dups, total = merge_wordlists(file1, file2, output_file)

    print("\n" + "="*80)
    print("MERGE COMPLETE")
    print("="*80)
    print(f"\nSummary:")
    print(f"  File 1: {count1} words")
    print(f"  File 2: {count2} words")
    print(f"  Duplicates: {dups} words")
    print(f"  Final merged list: {total} words")
    print(f"\nFiles created:")
    print(f"  1. {output_file}")
    print(f"  2. {output_file.replace('.txt', '_duplicates_report.txt')}")


if __name__ == "__main__":
    main()
