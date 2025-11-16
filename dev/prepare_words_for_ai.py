#!/usr/bin/env python3
"""
Prepare Words for AI Batch Processing
Extracts entry words from bible_crossword_v6.txt and splits into 500-word batches
"""

import os

# Configuration
INPUT_FILE = r"D:\Project_PP\projects\bible\dev\only_in_esv.txt"
OUTPUT_DIR = r"D:\Project_PP\projects\bible\dev\esv_ai_batches"
BATCH_SIZE = 500

def extract_words(input_file):
    """Extract first word from each line"""
    words = []
    
    print(f"Reading from: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Split by tab and get first field (the word)
            parts = line.split('\t')
            if parts:
                word = parts[0].strip()
                if word:
                    words.append(word)
    
    print(f"Extracted {len(words):,} words")
    return words

def create_batches(words, batch_size):
    """Split words into batches of specified size"""
    batches = []
    
    for i in range(0, len(words), batch_size):
        batch = words[i:i + batch_size]
        batches.append(batch)
    
    print(f"Created {len(batches)} batches of up to {batch_size} words")
    return batches

def write_batch_files(batches, output_dir):
    """Write batches to numbered files"""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    for batch_num, batch in enumerate(batches, start=1):
        # Format batch number with leading zeros (001, 002, etc.)
        filename = f"batch_{batch_num:03d}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Write numbered list
        with open(filepath, 'w', encoding='utf-8') as f:
            for word_num, word in enumerate(batch, start=1):
                f.write(f"{word_num}. {word}\n")
        
        print(f"  Wrote {filename}: {len(batch)} words")
    
    print(f"\nTotal files created: {len(batches)}")

def main():
    """Main execution"""
    print("="*70)
    print("PREPARE WORDS FOR AI BATCH PROCESSING")
    print("="*70)
    
    # Extract words from input file
    words = extract_words(INPUT_FILE)
    
    if not words:
        print("ERROR: No words extracted!")
        return
    
    # Create batches
    batches = create_batches(words, BATCH_SIZE)
    
    # Write batch files
    write_batch_files(batches, OUTPUT_DIR)
    
    print("\n" + "="*70)
    print("SUCCESS!")
    print("="*70)
    print(f"Total words: {len(words):,}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Total batches: {len(batches)}")
    print(f"Output location: {OUTPUT_DIR}")
    print("\nReady for AI processing!")

if __name__ == "__main__":
    main()