"""
Alphabetize kjv_complete_full.txt and verify format
Format: <WORD><tab><clue1><tab><clue2><tab><verse+citation>
"""

def process_file(input_file, output_file):
    """Read, verify format, and alphabetize entries"""

    print(f"Reading {input_file}...")
    entries = []
    invalid_lines = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            parts = line.split('\t')

            # Check format: should have exactly 4 fields
            if len(parts) == 4:
                word = parts[0].strip()
                clue1 = parts[1].strip()
                clue2 = parts[2].strip()
                verse_citation = parts[3].strip()

                if word:  # Make sure word is not empty
                    entries.append({
                        'word': word,
                        'clue1': clue1,
                        'clue2': clue2,
                        'verse_citation': verse_citation,
                        'line_num': line_num
                    })
                else:
                    invalid_lines.append((line_num, line, "Empty word"))
            else:
                invalid_lines.append((line_num, line, f"Expected 4 fields, got {len(parts)}"))

    print(f"  Loaded {len(entries)} valid entries")
    if invalid_lines:
        print(f"  Found {len(invalid_lines)} invalid lines")

    # Check for duplicates
    print("\nChecking for duplicates...")
    word_counts = {}
    for entry in entries:
        word = entry['word']
        if word in word_counts:
            word_counts[word].append(entry['line_num'])
        else:
            word_counts[word] = [entry['line_num']]

    duplicates = {word: lines for word, lines in word_counts.items() if len(lines) > 1}

    if duplicates:
        print(f"  Found {len(duplicates)} duplicate words:")
        for word, lines in sorted(duplicates.items())[:10]:
            print(f"    {word}: appears on lines {lines}")
        if len(duplicates) > 10:
            print(f"    ... and {len(duplicates) - 10} more duplicates")
    else:
        print("  No duplicates found")

    # Remove duplicates (keep first occurrence)
    print("\nRemoving duplicates (keeping first occurrence)...")
    seen_words = set()
    unique_entries = []

    for entry in entries:
        if entry['word'] not in seen_words:
            unique_entries.append(entry)
            seen_words.add(entry['word'])

    print(f"  Unique entries: {len(unique_entries)}")

    # Alphabetize
    print("\nAlphabetizing entries...")
    unique_entries.sort(key=lambda x: x['word'].upper())

    # Write output
    print(f"\nWriting to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in unique_entries:
            line = f"{entry['word']}\t{entry['clue1']}\t{entry['clue2']}\t{entry['verse_citation']}"
            f.write(line + '\n')

    print(f"  Successfully wrote {len(unique_entries)} entries")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total lines read: {len(entries) + len(invalid_lines)}")
    print(f"Valid entries: {len(entries)}")
    print(f"Invalid lines: {len(invalid_lines)}")
    print(f"Duplicate words: {len(duplicates)}")
    print(f"Unique entries written: {len(unique_entries)}")
    print(f"\nOutput file: {output_file}")

    # Show invalid lines if any
    if invalid_lines:
        print("\n" + "="*70)
        print("INVALID LINES:")
        print("="*70)
        for line_num, line, reason in invalid_lines[:20]:
            print(f"Line {line_num}: {reason}")
            print(f"  {line[:100]}...")
        if len(invalid_lines) > 20:
            print(f"  ... and {len(invalid_lines) - 20} more invalid lines")

    return len(unique_entries), len(duplicates), len(invalid_lines)

if __name__ == "__main__":
    input_file = r"D:\Project_PP\projects\bible\dev\kjv_complete_full.txt"
    output_file = r"D:\Project_PP\projects\bible\dev\kjv_complete_full.txt"

    print("="*70)
    print("ALPHABETIZE AND VERIFY KJV COMPLETE FILE")
    print("="*70)

    unique_count, dup_count, invalid_count = process_file(input_file, output_file)

    print("\n" + "="*70)
    print("VERIFICATION COMPLETE")
    print("="*70)

    if dup_count == 0 and invalid_count == 0:
        print("✓ All entries are valid and unique")
        print("✓ File is alphabetized")
        print(f"✓ Format verified: <WORD><tab><clue1><tab><clue2><tab><verse+citation>")
    else:
        if dup_count > 0:
            print(f"⚠ {dup_count} duplicates were removed")
        if invalid_count > 0:
            print(f"⚠ {invalid_count} invalid lines were skipped")
