#!/usr/bin/env python3
"""
Remove redundant ORIGINAL column from strongs entries in merged wordlist.
Converts 5-column format (WORD + ORIGINAL + 3 clues) to 4-column format (WORD + 3 clues).
"""


def fix_wordlist(input_file, output_file):
    """Remove the ORIGINAL column from entries that have it."""

    print(f"Reading {input_file}...")

    lines_with_5_cols = 0
    lines_with_4_cols = 0
    lines_fixed = 0

    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:

        for line_num, line in enumerate(f_in, 1):
            line = line.rstrip('\n')

            if not line.strip():
                f_out.write(line + '\n')
                continue

            parts = line.split('\t')

            if len(parts) == 5:
                # Format: WORD	ORIGINAL	CLUE1	CLUE2	CLUE3
                # Remove ORIGINAL (index 1)
                word = parts[0]
                clue1 = parts[2]  # Was MEANING
                clue2 = parts[3]  # Was ETYMOLOGY
                clue3 = parts[4]  # Was STRONGS

                # Write without ORIGINAL column
                new_line = f"{word}\t{clue1}\t{clue2}\t{clue3}"
                f_out.write(new_line + '\n')

                lines_with_5_cols += 1
                lines_fixed += 1

            elif len(parts) == 4:
                # Already in correct format: WORD	CLUE1	CLUE2	CLUE3
                f_out.write(line + '\n')
                lines_with_4_cols += 1

            else:
                # Unexpected format, keep as-is and warn
                f_out.write(line + '\n')
                print(f"  Warning: Line {line_num} has {len(parts)} columns (unexpected)")

            if line_num % 5000 == 0:
                print(f"  Processed {line_num} lines...")

    print(f"\nProcessing complete!")
    print(f"  Lines with 5 columns (fixed): {lines_with_5_cols}")
    print(f"  Lines with 4 columns (kept): {lines_with_4_cols}")
    print(f"  Total lines fixed: {lines_fixed}")

    return lines_with_5_cols, lines_with_4_cols


def main():
    input_file = r'D:\Project_PP\projects\bible\dev\strong_bible_list_v1.txt'
    output_file = r'D:\Project_PP\projects\bible\dev\strong_bible_list_v1_fixed.txt'

    print("="*80)
    print("FIXING REDUNDANT ORIGINAL COLUMN")
    print("="*80)
    print()

    fixed, kept = fix_wordlist(input_file, output_file)

    print("\n" + "="*80)
    print("FIX COMPLETE")
    print("="*80)
    print(f"\nOutput written to: {output_file}")
    print(f"\nSummary:")
    print(f"  Entries fixed (removed ORIGINAL column): {fixed}")
    print(f"  Entries kept as-is: {kept}")
    print(f"  Total entries: {fixed + kept}")


if __name__ == "__main__":
    main()
