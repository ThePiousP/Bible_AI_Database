#!/usr/bin/env python3
"""
Consolidate bible_crossword_v2.txt into proper crossword format
Converts from:
  WORD [TAB] none [TAB] clue [TAB] reference  (one line per verse)
To:
  WORD [TAB] clue1 [TAB] clue2 [TAB] clue3... (one line per word)
"""

import sys
from collections import defaultdict

INPUT_FILE = r"D:\Project_PP\Unity\Bible Crossword\Assets\Crossword\CrosswordBuilder\Data\bible_crossword_v2.txt"
OUTPUT_FILE = r"D:\Project_PP\Unity\Bible Crossword\Assets\Crossword\CrosswordBuilder\Data\bible_crossword_consolidated.txt"
MALFORMED_FILE = r"D:\Project_PP\Unity\Bible Crossword\malformed_entries.txt"

def consolidate_crossword_file():
    """Consolidate duplicate words into single entries with multiple clues"""
    print("="*70)
    print("BIBLE CROSSWORD CONSOLIDATION")
    print("="*70)
    print(f"Input: {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    word_clues = defaultdict(list)
    malformed_entries = []
    total_lines = 0
    skipped_lines = 0

    print("Reading and parsing entries...")

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1

            if total_lines % 5000 == 0:
                print(f"  Processed {total_lines:,} lines...")

            line = line.strip()
            if not line:
                skipped_lines += 1
                continue

            parts = line.split('\t')

            # Check if this is a malformed entry (clue in first column)
            if len(parts) >= 2 and '___' in parts[0]:
                malformed_entries.append({
                    'line_num': line_num,
                    'content': line,
                    'parts': parts
                })
                skipped_lines += 1
                continue

            # Parse normal entries
            if len(parts) < 2:
                skipped_lines += 1
                continue

            word = parts[0].strip().upper()

            # Skip empty words
            if not word:
                skipped_lines += 1
                continue

            # Combine clue and reference
            # Format: "clue text (reference)"
            if len(parts) == 2:
                # Just word and clue
                clue = parts[1].strip()
            elif len(parts) == 3:
                # word [TAB] clue [TAB] reference
                # or word [TAB] "none" [TAB] clue_with_reference
                col2 = parts[1].strip()
                col3 = parts[2].strip()

                if col2.lower() == 'none':
                    # Format: word [TAB] none [TAB] clue_with_reference
                    clue = col3
                else:
                    # Format: word [TAB] clue [TAB] reference
                    clue = f"{col2} ({col3})"
            elif len(parts) == 4:
                # word [TAB] none [TAB] clue [TAB] reference
                clue_text = parts[2].strip()
                reference = parts[3].strip()
                clue = f"{clue_text} ({reference})"
            else:
                # More than 4 parts - combine everything after word
                clue = '\t'.join(parts[1:])

            # Only add non-empty clues
            if clue and clue.lower() != 'none':
                word_clues[word].append(clue)

    print(f"\nParsing complete:")
    print(f"  Total lines read: {total_lines:,}")
    print(f"  Skipped/malformed: {skipped_lines:,}")
    print(f"  Unique words found: {len(word_clues):,}")
    print(f"  Malformed entries found: {len(malformed_entries)}")

    # Save malformed entries for manual review
    if malformed_entries:
        print(f"\nSaving malformed entries to: {MALFORMED_FILE}")
        with open(MALFORMED_FILE, 'w', encoding='utf-8') as f:
            f.write("MALFORMED ENTRIES REPORT\n")
            f.write("="*70 + "\n\n")
            f.write(f"Found {len(malformed_entries)} entries where the clue appears in column 1\n")
            f.write("These need manual correction to determine the answer word.\n\n")

            for entry in malformed_entries:
                f.write(f"Line {entry['line_num']}:\n")
                f.write(f"  Content: {entry['content']}\n")
                f.write(f"  Columns: {len(entry['parts'])}\n")
                f.write(f"  Column 1: {entry['parts'][0][:80]}...\n")
                if len(entry['parts']) > 1:
                    f.write(f"  Column 2: {entry['parts'][1]}\n")
                f.write("\n")
        print(f"  Saved {len(malformed_entries)} malformed entries")

    # Write consolidated output
    print(f"\nWriting consolidated output...")

    total_clues = 0
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for word in sorted(word_clues.keys()):
            clues = word_clues[word]
            total_clues += len(clues)

            # Write: WORD [TAB] clue1 [TAB] clue2 [TAB] clue3...
            line = word + '\t' + '\t'.join(clues) + '\n'
            f.write(line)

    print(f"\nConsolidation complete!")
    print("="*70)
    print(f"SUCCESS!")
    print(f"  Unique words: {len(word_clues):,}")
    print(f"  Total clues: {total_clues:,}")
    print(f"  Average clues per word: {total_clues/len(word_clues):.2f}")
    print(f"\nOutput saved to: {OUTPUT_FILE}")
    if malformed_entries:
        print(f"Malformed entries saved to: {MALFORMED_FILE}")
    print("="*70)

    return len(word_clues), total_clues, len(malformed_entries)

if __name__ == "__main__":
    consolidate_crossword_file()
