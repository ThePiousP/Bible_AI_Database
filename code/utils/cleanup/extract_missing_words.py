"""
Extract missing words from kjv_merge_output.txt
"""

missing_words = []

with open('kjv_merge_output.txt', 'r', encoding='utf-8') as f:
    for line in f:
        if 'MISSING in batch files:' in line:
            word = line.split('MISSING in batch files:')[1].strip()
            missing_words.append(word)

# Sort the words
missing_words.sort()

# Write to file
with open('missing_words_kjv.txt', 'w', encoding='utf-8') as f:
    f.write(f"Missing Words from KJV Batch Files\n")
    f.write(f"Total: {len(missing_words)} words\n")
    f.write("="*70 + "\n\n")

    for word in missing_words:
        f.write(word + "\n")

print(f"Extracted {len(missing_words)} missing words")
print(f"Saved to: missing_words_kjv.txt")
