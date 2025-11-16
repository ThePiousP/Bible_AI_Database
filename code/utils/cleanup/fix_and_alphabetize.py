"""
Fix format issues, alphabetize, and verify kjv_complete_full.txt
Format: <WORD><tab><clue1><tab><clue2><tab><verse+citation>
"""

def process_file(input_file, output_file):
    """Read, fix format, and alphabetize entries"""

    print(f"Reading {input_file}...")
    entries = []
    skipped_lines = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            parts = line.split('\t')

            # Need at least 4 fields
            if len(parts) >= 4:
                word = parts[0].strip()
                clue1 = parts[1].strip()
                clue2 = parts[2].strip()

                # If there are more than 4 fields, combine everything from field 4 onwards
                if len(parts) > 4:
                    verse_citation = '\t'.join(parts[3:])
                else:
                    verse_citation = parts[3].strip()

                if word:  # Make sure word is not empty
                    entries.append({
                        'word': word,
                        'clue1': clue1,
                        'clue2': clue2,
                        'verse_citation': verse_citation,
                        'original_line': line_num
                    })
                else:
                    skipped_lines.append((line_num, line, "Empty word"))
            else:
                skipped_lines.append((line_num, line, f"Only {len(parts)} fields (need at least 4)"))

    print(f"  Loaded {len(entries)} entries")
    if skipped_lines:
        print(f"  Skipped {len(skipped_lines)} invalid lines")

    # Check for duplicates
    print("\nChecking for duplicates...")
    word_counts = {}
    for entry in entries:
        word = entry['word']
        if word in word_counts:
            word_counts[word].append(entry['original_line'])
        else:
            word_counts[word] = [entry['original_line']]

    duplicates = {word: lines for word, lines in word_counts.items() if len(lines) > 1}

    if duplicates:
        print(f"  Found {len(duplicates)} duplicate words:")
        for i, (word, lines) in enumerate(sorted(duplicates.items())[:10], 1):
            print(f"    {i}. {word}: lines {lines}")
        if len(duplicates) > 10:
            print(f"    ... and {len(duplicates) - 10} more")
    else:
        print("  No duplicates found")

    # Remove duplicates (keep first occurrence)
    if duplicates:
        print("\nRemoving duplicates (keeping first occurrence)...")
        seen_words = set()
        unique_entries = []

        for entry in entries:
            if entry['word'] not in seen_words:
                unique_entries.append(entry)
                seen_words.add(entry['word'])

        print(f"  Removed {len(entries) - len(unique_entries)} duplicate entries")
        entries = unique_entries

    # Alphabetize
    print("\nAlphabetizing entries...")
    entries.sort(key=lambda x: x['word'].upper())

    # Write output
    print(f"\nWriting to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in entries:
            # Ensure no tabs in verse_citation except what was intentionally there
            verse_citation = entry['verse_citation'].replace('\t', ' ')
            line = f"{entry['word']}\t{entry['clue1']}\t{entry['clue2']}\t{verse_citation}"
            f.write(line + '\n')

    print(f"  Successfully wrote {len(entries)} entries")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Original lines: {len(entries) + len(skipped_lines) + len(duplicates)}")
    print(f"Valid entries: {len(entries)}")
    print(f"Skipped lines: {len(skipped_lines)}")
    print(f"Duplicate words removed: {len(duplicates)}")
    print(f"\nFinal count: {len(entries)} unique entries")
    print(f"Output file: {output_file}")

    # Show skipped lines if any
    if skipped_lines:
        print("\n" + "="*70)
        print("SKIPPED LINES (first 20):")
        print("="*70)
        for line_num, line, reason in skipped_lines[:20]:
            print(f"Line {line_num}: {reason}")
            print(f"  Content: {line[:80]}...")

    return len(entries), len(duplicates), len(skipped_lines)

if __name__ == "__main__":
    input_file = r"D:\Project_PP\projects\bible\dev\kjv_complete_full.txt"
    output_file = r"D:\Project_PP\projects\bible\dev\kjv_complete_full.txt"

    print("="*70)
    print("FIX AND ALPHABETIZE KJV COMPLETE FILE")
    print("="*70)

    final_count, dup_count, skip_count = process_file(input_file, output_file)

    print("\n" + "="*70)
    print("VERIFICATION COMPLETE")
    print("="*70)

    if dup_count == 0 and skip_count == 0:
        print("[OK] All entries are valid and unique")
        print("[OK] File is alphabetized")
        print("[OK] Format verified: <WORD><tab><clue1><tab><clue2><tab><verse+citation>")
    else:
        if dup_count > 0:
            print(f"[WARN] {dup_count} duplicates were removed")
        if skip_count > 0:
            print(f"[WARN] {skip_count} invalid lines were skipped")

    print(f"\nFinal entry count: {final_count}")
