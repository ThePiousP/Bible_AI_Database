"""
Merge missing_words_clues.txt with bible_crossword_v6.txt entries
and add them to kjv_complete.txt
"""
import re

def parse_missing_clues(clues_file):
    """Parse missing_words_clues.txt to get word -> (clue1, clue2)"""
    clues_data = {}

    print(f"Reading {clues_file}...")
    with open(clues_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) >= 3:
                word = parts[0].strip()
                clue1 = parts[1].strip()
                clue2 = parts[2].strip()
                clues_data[word] = (clue1, clue2)
            elif len(parts) == 2:
                word = parts[0].strip()
                clue1 = parts[1].strip()
                clue2 = ""
                clues_data[word] = (clue1, clue2)

    print(f"  Loaded {len(clues_data)} words with clues")
    return clues_data

def parse_v6_file(v6_file):
    """Parse bible_crossword_v6.txt to get word -> (verse, citation)"""
    v6_data = {}

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
                    citation = ""
                    verse = verse_and_citation

                v6_data[word] = (verse, citation)

    print(f"  Loaded {len(v6_data)} words from v6")
    return v6_data

def merge_and_create_complete(clues_data, v6_data, existing_kjv_file, output_file):
    """Merge the data and create complete file"""
    print("\nMerging missing entries...")

    missing_entries = []
    words_not_in_v6 = []

    for word in clues_data:
        if word in v6_data:
            clue1, clue2 = clues_data[word]
            verse, citation = v6_data[word]

            missing_entries.append({
                'word': word,
                'clue1': clue1,
                'clue2': clue2,
                'verse': verse,
                'citation': citation
            })
        else:
            words_not_in_v6.append(word)
            print(f"  WARNING: {word} not found in bible_crossword_v6.txt")

    print(f"\n  Successfully matched: {len(missing_entries)} entries")
    print(f"  Not found in v6: {len(words_not_in_v6)} entries")

    # Read existing kjv_complete.txt
    print(f"\nReading existing {existing_kjv_file}...")
    existing_entries = []
    with open(existing_kjv_file, 'r', encoding='utf-8') as f:
        for line in f:
            existing_entries.append(line.rstrip('\n'))

    print(f"  Existing entries: {len(existing_entries)}")

    # Combine and sort all entries
    print("\nCombining all entries...")
    all_entries = []

    # Add existing entries
    for line in existing_entries:
        parts = line.split('\t')
        if len(parts) >= 5:
            all_entries.append({
                'word': parts[0].strip(),
                'clue1': parts[1].strip(),
                'clue2': parts[2].strip(),
                'verse': parts[3].strip(),
                'citation': parts[4].strip()
            })

    # Add missing entries
    all_entries.extend(missing_entries)

    # Sort alphabetically by word
    all_entries.sort(key=lambda x: x['word'])

    # Write to output file
    print(f"\nWriting complete file to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in all_entries:
            line = f"{entry['word']}\t{entry['clue1']}\t{entry['clue2']}\t{entry['verse']}\t{entry['citation']}"
            f.write(line + '\n')

    print(f"  Successfully wrote {len(all_entries)} total entries")

    return len(missing_entries), words_not_in_v6

def main():
    clues_file = r"D:\Project_PP\projects\bible\missing_words_clues.txt"
    v6_file = r"D:\Project_PP\projects\bible\bible_crossword_v6.txt"
    existing_kjv_file = r"D:\Project_PP\projects\bible\dev\kjv_complete.txt"
    output_file = r"D:\Project_PP\projects\bible\dev\kjv_complete_full.txt"

    print("="*70)
    print("COMPLETING KJV DATASET")
    print("="*70)

    # Parse files
    clues_data = parse_missing_clues(clues_file)
    v6_data = parse_v6_file(v6_file)

    # Merge and create complete file
    added_count, not_found = merge_and_create_complete(clues_data, v6_data, existing_kjv_file, output_file)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Previous total: 12,524 entries")
    print(f"Missing entries added: {added_count}")
    print(f"New total: 12,524 + {added_count} = {12524 + added_count}")
    print(f"\nOutput file: {output_file}")

    if not_found:
        print(f"\nWARNING: {len(not_found)} words not found in bible_crossword_v6.txt:")
        for word in not_found[:10]:
            print(f"  - {word}")
        if len(not_found) > 10:
            print(f"  ... and {len(not_found) - 10} more")

if __name__ == "__main__":
    main()
