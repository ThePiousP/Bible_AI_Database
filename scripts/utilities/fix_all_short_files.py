#!/usr/bin/env python3
"""
Fix ALL files with 10 or fewer lines using multiple strategies
"""

from pathlib import Path
import re

def fix_text_multi_strategy(text):
    """
    Apply multiple strategies to add line breaks:
    1. After periods/question marks/exclamation marks + space
    2. Every ~150 words if still single line
    3. At paragraph breaks (double spaces, "And", "But", "Now", etc.)
    """

    original_line_count = text.count('\n') + 1

    # Strategy 1: Add breaks after punctuation
    # Protect common abbreviations
    abbreviations = [
        r'vs\.',  r'Rev\.',  r'Dr\.',  r'Mr\.',  r'Mrs\.',  r'Ms\.',
        r'St\.',  r'Jr\.',  r'Sr\.',  r'ch\.',  r'Ps\.',  r'Mt\.',
        r'Mk\.',  r'Lk\.',  r'Jn\.',  r'Gen\.',  r'Ex\.',  r'Lev\.',
        r'Num\.',  r'Deut\.',  r'Josh\.',  r'Matt\.',  r'etc\.',
        r'i\.e\.',  r'e\.g\.',  r'vol\.',  r'p\.',  r'pp\.',
    ]

    # Replace abbreviations temporarily
    for i, abbr in enumerate(abbreviations):
        placeholder = f'__ABBR{i}__'
        text = re.sub(abbr, placeholder, text, flags=re.IGNORECASE)

    # Add breaks after sentence-ending punctuation
    text = re.sub(r'([.!?])\s+', r'\1\n', text)

    # Restore abbreviations
    for i, abbr in enumerate(abbreviations):
        placeholder = f'__ABBR{i}__'
        original = abbr.replace('\\', '')
        text = text.replace(placeholder, original)

    # Strategy 2: If still very few lines, add breaks at discourse markers
    new_line_count = text.count('\n') + 1
    if new_line_count < 20:
        # Add breaks before common discourse markers when preceded by space
        discourse_markers = [
            r' And ',
            r' But ',
            r' Now ',
            r' So ',
            r' Then ',
            r' Therefore ',
            r' However ',
            r' Moreover ',
            r' Furthermore ',
            r' Nevertheless ',
            r' Thus ',
            r' Hence ',
            r' Yet ',
        ]

        for marker in discourse_markers:
            # Only add break if marker is not at start of existing line
            pattern = f'(?<!\n){re.escape(marker)}'
            text = re.sub(pattern, '\n' + marker.strip() + ' ', text, flags=re.IGNORECASE)

    # Strategy 3: If STILL too few lines (< 10), chunk by word count
    new_line_count = text.count('\n') + 1
    if new_line_count < 10:
        words = text.split()
        chunks = []
        current_chunk = []
        word_limit = 100  # ~100 words per line

        for word in words:
            current_chunk.append(word)
            if len(current_chunk) >= word_limit:
                # Try to break at a sentence end
                chunk_text = ' '.join(current_chunk)
                # Look for last sentence end
                last_period = max(chunk_text.rfind('. '), chunk_text.rfind('? '), chunk_text.rfind('! '))
                if last_period > 50:  # If found reasonably far in
                    chunks.append(chunk_text[:last_period+1])
                    # Put remainder back
                    remainder = chunk_text[last_period+1:].strip().split()
                    current_chunk = remainder
                else:
                    chunks.append(chunk_text)
                    current_chunk = []

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        text = '\n'.join(chunks)

    # Clean up: remove very short lines (< 10 chars) by rejoining
    lines = [line.strip() for line in text.split('\n')]
    cleaned_lines = []
    buffer = ''

    for line in lines:
        if len(line) < 10 and buffer:
            buffer += ' ' + line
        else:
            if buffer:
                cleaned_lines.append(buffer)
            buffer = line

    if buffer:
        cleaned_lines.append(buffer)

    return '\n'.join(cleaned_lines)

def fix_file(file_path):
    """Fix a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        original_lines = text.count('\n') + 1

        # Only process files with 10 or fewer lines
        if original_lines <= 10:
            fixed_text = fix_text_multi_strategy(text)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_text)

            new_lines = fixed_text.count('\n') + 1

            return {
                'file': file_path.name,
                'original_lines': original_lines,
                'new_lines': new_lines,
                'lines_added': new_lines - original_lines,
                'success': True
            }
        else:
            return {'file': file_path.name, 'skipped': True}

    except Exception as e:
        return {
            'file': file_path.name,
            'error': str(e),
            'success': False
        }

def main():
    """Fix all files with 10 or fewer lines"""

    cleaned_dir = Path(r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts_cleaned')
    all_files = list(cleaned_dir.glob('*.txt'))

    print(f"FIXING ALL SHORT FILES (10 or fewer lines)")
    print("=" * 80)
    print(f"Total files: {len(all_files)}")
    print("\nProcessing...\n")

    stats = {
        'processed': 0,
        'skipped': 0,
        'errors': 0,
        'total_lines_added': 0,
    }

    results = []

    for file_path in all_files:
        result = fix_file(file_path)

        if result.get('success'):
            stats['processed'] += 1
            stats['total_lines_added'] += result['lines_added']
            results.append(result)

            if stats['processed'] % 10 == 0:
                print(f"Processed {stats['processed']} files, added {stats['total_lines_added']:,} lines")

        elif result.get('error'):
            stats['errors'] += 1
            print(f"ERROR: {result['file']} - {result['error']}")
        else:
            stats['skipped'] += 1

    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)

    print(f"\nFiles fixed: {stats['processed']}")
    print(f"Files skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")

    if stats['processed'] > 0:
        print(f"\nTotal lines added: {stats['total_lines_added']:,}")
        print(f"Average lines added per file: {stats['total_lines_added'] / stats['processed']:.1f}")

        # Show top 20
        results.sort(key=lambda x: x['lines_added'], reverse=True)
        print(f"\nTOP 20 FILES BY LINES ADDED:")
        for i, r in enumerate(results[:20], 1):
            print(f"  {i:2}. {r['file'][:60]:60} | {r['original_lines']:2} -> {r['new_lines']:3} lines (+{r['lines_added']:3})")

if __name__ == '__main__':
    main()
