"""
Merge batch files with bible_crossword_v6.txt to create kjv_complete.txt
Format: <WORD><tab><clue 1><tab><clue 2><tab><clue 3 - verse><tab><clue 4 - citation>
"""
import os
import re
from pathlib import Path

def parse_batch_files(batch_dir):
    """Parse all batch files and return a dict of WORD -> (clue1, clue2)"""
    batch_data = {}
    batch_files = sorted(Path(batch_dir).glob("batch_*.txt"))

    print(f"Reading {len(batch_files)} batch files...")
    for batch_file in batch_files:
        print(f"  Reading {batch_file.name}...")
        with open(batch_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) >= 3:
                    word = parts[0].strip()
                    clue1 = parts[1].strip()
                    clue2 = parts[2].strip()

                    if word in batch_data:
                        print(f"    WARNING: Duplicate word '{word}' in {batch_file.name} line {line_num}")

                    batch_data[word] = (clue1, clue2)
                elif len(parts) == 2:
                    word = parts[0].strip()
                    clue1 = parts[1].strip()
                    clue2 = ""
                    batch_data[word] = (clue1, clue2)
                else:
                    print(f"    WARNING: Invalid format in {batch_file.name} line {line_num}: {line}")

    print(f"Total words from batch files: {len(batch_data)}")
    return batch_data

def parse_v6_file(v6_file):
    """Parse bible_crossword_v6.txt and return list of (word, verse, citation)"""
    v6_data = []

    print(f"\nReading {v6_file}...")
    with open(v6_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            if not line:
                continue

            parts = line.split('\t')
            if len(parts) >= 2:
                word = parts[0].strip()
                verse_and_citation = parts[1].strip()

                # Extract citation (text in parentheses at the end)
                citation_match = re.search(r'\(([^)]+)\)\s*$', verse_and_citation)
                if citation_match:
                    citation = citation_match.group(1)
                    verse = verse_and_citation[:citation_match.start()].strip()
                else:
                    # No citation found
                    citation = ""
                    verse = verse_and_citation

                v6_data.append((word, verse, citation))
            else:
                print(f"  WARNING: Invalid format in line {line_num}: {line}")

    print(f"Total words from bible_crossword_v6.txt: {len(v6_data)}")
    return v6_data

def merge_data(batch_data, v6_data):
    """Merge batch and v6 data"""
    merged = []
    missing_words = []
    extra_words = []

    print("\nMerging data...")

    # Track which batch words we've used
    used_batch_words = set()

    for word, verse, citation in v6_data:
        if word in batch_data:
            clue1, clue2 = batch_data[word]
            merged.append({
                'word': word,
                'clue1': clue1,
                'clue2': clue2,
                'verse': verse,
                'citation': citation
            })
            used_batch_words.add(word)
        else:
            missing_words.append(word)
            print(f"  MISSING in batch files: {word}")

    # Find words in batch files but not in bible_crossword_v6.txt
    for word in batch_data:
        if word not in used_batch_words:
            extra_words.append(word)

    return merged, missing_words, extra_words

def write_output(merged, output_file):
    """Write merged data to output file"""
    print(f"\nWriting to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in merged:
            line = f"{entry['word']}\t{entry['clue1']}\t{entry['clue2']}\t{entry['verse']}\t({entry['citation']})"
            f.write(line + '\n')

    print(f"Successfully wrote {len(merged)} entries to {output_file}")

def main():
    batch_dir = r"D:\Project_PP\projects\bible\dev\ai_batches"
    v6_file = r"D:\Project_PP\projects\bible\bible_crossword_v6.txt"
    output_file = r"D:\Project_PP\projects\bible\dev\kjv_complete.txt"

    print("="*70)
    print("KJV DATA MERGER")
    print("="*70)

    # Parse batch files
    batch_data = parse_batch_files(batch_dir)

    # Parse bible_crossword_v6.txt
    v6_data = parse_v6_file(v6_file)

    # Merge
    merged, missing_words, extra_words = merge_data(batch_data, v6_data)

    # Write output
    write_output(merged, output_file)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total entries successfully merged: {len(merged)}")
    print(f"Words in bible_crossword_v6.txt but MISSING from batch files: {len(missing_words)}")
    print(f"Words in batch files but NOT in bible_crossword_v6.txt: {len(extra_words)}")

    if missing_words:
        print("\n" + "="*70)
        print(f"MISSING WORDS ({len(missing_words)} total):")
        print("="*70)
        for word in sorted(missing_words):
            print(f"  - {word}")

    if extra_words:
        print("\n" + "="*70)
        print(f"EXTRA WORDS in batch files ({len(extra_words)} total):")
        print("="*70)
        for word in sorted(extra_words):
            clue1, clue2 = batch_data[word]
            print(f"  - {word}: {clue1} | {clue2}")

    if len(missing_words) == 0 and len(extra_words) == 0:
        print("\nPERFECT MATCH! All words aligned correctly.")

if __name__ == "__main__":
    main()
