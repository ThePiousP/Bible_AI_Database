"""
Compare two crossword word list files for duplicates.
"""

def analyze_files(file1, file2):
    """
    Analyze two files for duplicates based on the first WORD in each line.
    """
    print(f"Reading {file1}...")
    with open(file1, 'r', encoding='utf-8') as f:
        v6_lines = [line.strip() for line in f if line.strip()]

    print(f"Reading {file2}...")
    with open(file2, 'r', encoding='utf-8') as f:
        esv_lines = [line.strip() for line in f if line.strip()]

    # Extract first word from each line (before tab or space)
    def get_first_word(line):
        # Split by tab first, then by space if no tab
        if '\t' in line:
            return line.split('\t')[0].strip()
        else:
            return line.split()[0].strip() if line.split() else ''

    v6_words = [get_first_word(line) for line in v6_lines]
    esv_words = [get_first_word(line) for line in esv_lines]

    # Convert to sets for comparison
    v6_set = set(v6_words)
    esv_set = set(esv_words)

    # Find duplicates
    duplicates = v6_set & esv_set

    # Find unique entries
    only_in_v6 = v6_set - esv_set
    only_in_esv = esv_set - v6_set

    # Statistics
    print("\n" + "="*70)
    print("FILE STATISTICS (comparing first WORD only)")
    print("="*70)
    print(f"bible_crossword_v6.txt:")
    print(f"  Total lines: {len(v6_lines):,}")
    print(f"  Total words: {len(v6_words):,}")
    print(f"  Unique words: {len(v6_set):,}")
    print(f"  Duplicate words within file: {len(v6_words) - len(v6_set):,}")

    print(f"\nesv_crossword_master.txt:")
    print(f"  Total lines: {len(esv_lines):,}")
    print(f"  Total words: {len(esv_words):,}")
    print(f"  Unique words: {len(esv_set):,}")
    print(f"  Duplicate words within file: {len(esv_words) - len(esv_set):,}")

    print("\n" + "="*70)
    print("COMPARISON RESULTS")
    print("="*70)
    print(f"Words in BOTH files (duplicates): {len(duplicates):,}")
    print(f"Words ONLY in v6: {len(only_in_v6):,}")
    print(f"Words ONLY in ESV: {len(only_in_esv):,}")
    print(f"Total unique words (merged): {len(v6_set | esv_set):,}")

    # Create mappings from word to full line for showing examples
    v6_word_to_line = {get_first_word(line): line for line in v6_lines}
    esv_word_to_line = {get_first_word(line): line for line in esv_lines}

    # Show some examples
    if duplicates:
        print("\n" + "="*70)
        print("SAMPLE DUPLICATE WORDS (first 20):")
        print("="*70)
        for i, word in enumerate(sorted(list(duplicates))[:20], 1):
            print(f"{i:3}. {word}")
            if word in v6_word_to_line:
                v6_entry = v6_word_to_line[word]
                print(f"      V6:  {v6_entry[:100]}{'...' if len(v6_entry) > 100 else ''}")
            if word in esv_word_to_line:
                esv_entry = esv_word_to_line[word]
                print(f"      ESV: {esv_entry[:100]}{'...' if len(esv_entry) > 100 else ''}")
            print()

    if only_in_v6:
        print("\n" + "="*70)
        print("SAMPLE WORDS ONLY IN V6 (first 20):")
        print("="*70)
        for i, word in enumerate(sorted(list(only_in_v6))[:20], 1):
            v6_entry = v6_word_to_line.get(word, word)
            print(f"{i:3}. {v6_entry[:120]}{'...' if len(v6_entry) > 120 else ''}")

    if only_in_esv:
        print("\n" + "="*70)
        print("SAMPLE WORDS ONLY IN ESV (first 20):")
        print("="*70)
        for i, word in enumerate(sorted(list(only_in_esv))[:20], 1):
            esv_entry = esv_word_to_line.get(word, word)
            print(f"{i:3}. {esv_entry[:120]}{'...' if len(esv_entry) > 120 else ''}")

    # Save full duplicate list with both entries
    duplicate_file = "duplicates_list.txt"
    with open(duplicate_file, 'w', encoding='utf-8') as f:
        f.write(f"Total duplicate words: {len(duplicates)}\n")
        f.write("="*70 + "\n\n")
        for word in sorted(duplicates):
            f.write(f"{word}\n")
            if word in v6_word_to_line:
                f.write(f"  V6:  {v6_word_to_line[word]}\n")
            if word in esv_word_to_line:
                f.write(f"  ESV: {esv_word_to_line[word]}\n")
            f.write("\n")
    print(f"\n[OK] Full duplicate list saved to: {duplicate_file}")

    # Save unique words lists
    v6_unique_file = "only_in_v6.txt"
    with open(v6_unique_file, 'w', encoding='utf-8') as f:
        f.write(f"Total unique words in v6: {len(only_in_v6)}\n")
        f.write("="*70 + "\n\n")
        for word in sorted(only_in_v6):
            if word in v6_word_to_line:
                f.write(v6_word_to_line[word] + "\n")
    print(f"[OK] V6 unique words saved to: {v6_unique_file}")

    esv_unique_file = "only_in_esv.txt"
    with open(esv_unique_file, 'w', encoding='utf-8') as f:
        f.write(f"Total unique words in ESV: {len(only_in_esv)}\n")
        f.write("="*70 + "\n\n")
        for word in sorted(only_in_esv):
            if word in esv_word_to_line:
                f.write(esv_word_to_line[word] + "\n")
    print(f"[OK] ESV unique words saved to: {esv_unique_file}")

    return {
        'v6_set': v6_set,
        'esv_set': esv_set,
        'duplicates': duplicates,
        'only_in_v6': only_in_v6,
        'only_in_esv': only_in_esv
    }


if __name__ == "__main__":
    file1 = r"D:\Project_PP\projects\bible\bible_crossword_v6.txt"
    file2 = r"D:\Project_PP\projects\bible\data\esv_crossword_master.txt"

    results = analyze_files(file1, file2)
