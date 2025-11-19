#!/usr/bin/env python3
"""
Fix remaining single-line files with a more aggressive approach
"""

from pathlib import Path
import re

def add_line_breaks_aggressive(text):
    """
    Add line breaks more aggressively:
    - After periods followed by space
    - After question marks followed by space
    - After exclamation marks followed by space
    - But avoid common abbreviations
    """

    # Common abbreviations
    abbreviations = [
        r'vs\.',
        r'Rev\.',
        r'Dr\.',
        r'Mr\.',
        r'Mrs\.',
        r'Ms\.',
        r'St\.',
        r'Jr\.',
        r'Sr\.',
        r'ch\.',
        r'Ps\.',
        r'Mt\.',
        r'Mk\.',
        r'Lk\.',
        r'Jn\.',
        r'Gen\.',
        r'Ex\.',
        r'Lev\.',
        r'Num\.',
        r'Deut\.',
        r'Josh\.',
        r'Matt\.',
        r'etc\.',
        r'i\.e\.',
        r'e\.g\.',
        r'vol\.',
        r'p\.',
        r'pp\.',
    ]

    # Temporarily replace abbreviations
    for i, abbr in enumerate(abbreviations):
        placeholder = f'__ABBR{i}__'
        text = re.sub(abbr, placeholder, text, flags=re.IGNORECASE)

    # Add line breaks after sentence-ending punctuation + space
    # Even if not followed by capital letter
    text = re.sub(r'([.!?])\s+', r'\1\n', text)

    # Restore abbreviations
    for i, abbr in enumerate(abbreviations):
        placeholder = f'__ABBR{i}__'
        original = abbr.replace('\\', '')
        text = text.replace(placeholder, original)

    # Clean up any lines that are too short (less than 10 chars) - rejoin them
    lines = text.split('\n')
    cleaned_lines = []
    buffer = ''

    for line in lines:
        line = line.strip()
        if len(line) < 10 and buffer:
            # Too short, add to buffer
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

        # Only process files with 1-5 lines
        if original_lines <= 5:
            fixed_text = add_line_breaks_aggressive(text)

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
            return {
                'file': file_path.name,
                'skipped': True
            }

    except Exception as e:
        return {
            'file': file_path.name,
            'error': str(e),
            'success': False
        }

def main():
    """Fix all files with 1-5 lines"""

    cleaned_dir = Path(r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts_cleaned')
    all_files = list(cleaned_dir.glob('*.txt'))

    print(f"FIXING REMAINING SINGLE-LINE FILES")
    print("=" * 80)
    print(f"Total files: {len(all_files)}")
    print("\nProcessing files with 1-5 lines...\n")

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
                print(f"Processed {stats['processed']} files...")

        elif result.get('error'):
            stats['errors'] += 1
            print(f"ERROR: {result['file']} - {result['error']}")
        else:
            stats['skipped'] += 1

    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)

    print(f"\nFiles with 1-5 lines fixed: {stats['processed']}")
    print(f"Files skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")

    if stats['processed'] > 0:
        print(f"\nTotal lines added: {stats['total_lines_added']:,}")
        print(f"Average lines added per file: {stats['total_lines_added'] / stats['processed']:.1f}")

        # Show top 10
        results.sort(key=lambda x: x['lines_added'], reverse=True)
        print(f"\nTOP 10 FILES BY LINES ADDED:")
        for i, r in enumerate(results[:10], 1):
            print(f"  {i}. {r['file']}: {r['original_lines']} -> {r['new_lines']} lines (+{r['lines_added']})")

if __name__ == '__main__':
    main()
