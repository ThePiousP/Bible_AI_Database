#!/usr/bin/env python3
"""
Fix single-line transcript files by adding line breaks at sentence boundaries
"""

from pathlib import Path
import re

def add_sentence_breaks(text):
    """
    Add line breaks at sentence boundaries

    Strategy:
    - Add break after period/question mark/exclamation followed by space and capital letter
    - Preserve paragraph structure where double spaces might exist
    - Handle common abbreviations (vs., Rev., Dr., etc.)
    """

    # Common abbreviations that shouldn't trigger a break
    abbreviations = [
        r'vs\.',
        r'Rev\.',
        r'Dr\.',
        r'Mr\.',
        r'Mrs\.',
        r'St\.',
        r'Jr\.',
        r'Sr\.',
        r'ch\.',
        r'Ps\.',
        r'Mt\.',
        r'Mk\.',
        r'Lk\.',
        r'Jn\.',
        r'etc\.',
        r'i\.e\.',
        r'e\.g\.',
    ]

    # Temporarily replace abbreviations with placeholders
    for i, abbr in enumerate(abbreviations):
        placeholder = f'__ABBR{i}__'
        text = re.sub(abbr, placeholder, text, flags=re.IGNORECASE)

    # Add line breaks after sentence-ending punctuation followed by capital letter
    # Pattern: (. or ? or !) + (one or more spaces) + (capital letter)
    text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\2', text)

    # Restore abbreviations
    for i, abbr in enumerate(abbreviations):
        placeholder = f'__ABBR{i}__'
        original = abbr.replace('\\', '')
        text = text.replace(placeholder, original)

    return text

def fix_file(file_path):
    """Fix a single file by adding sentence breaks"""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        original_lines = text.count('\n') + 1

        # Only process if it's a single-line file
        if original_lines == 1:
            # Add sentence breaks
            fixed_text = add_sentence_breaks(text)

            # Write back
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
                'skipped': True,
                'reason': f'Already has {original_lines} lines'
            }

    except Exception as e:
        return {
            'file': file_path.name,
            'error': str(e),
            'success': False
        }

def main():
    """Fix all single-line files"""

    cleaned_dir = Path(r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts_cleaned')

    # Get all transcript files
    all_files = list(cleaned_dir.glob('*.txt'))

    print(f"FIXING SINGLE-LINE TRANSCRIPT FILES")
    print("=" * 80)
    print(f"Directory: {cleaned_dir}")
    print(f"Total files: {len(all_files)}")
    print("\nProcessing...\n")

    # Statistics
    stats = {
        'processed': 0,
        'skipped': 0,
        'errors': 0,
        'total_lines_added': 0,
    }

    results = []
    errors = []

    for file_path in all_files:
        result = fix_file(file_path)

        if result.get('success'):
            stats['processed'] += 1
            stats['total_lines_added'] += result['lines_added']
            results.append(result)

            if stats['processed'] % 10 == 0:
                print(f"Processed {stats['processed']} files, added {stats['total_lines_added']:,} lines")

        elif result.get('skipped'):
            stats['skipped'] += 1
        else:
            stats['errors'] += 1
            errors.append(result)
            print(f"ERROR: {result['file']} - {result['error']}")

    # Print summary
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)

    print(f"\nTotal files checked: {len(all_files)}")
    print(f"Single-line files fixed: {stats['processed']}")
    print(f"Files skipped (already multi-line): {stats['skipped']}")
    print(f"Errors: {stats['errors']}")

    if stats['processed'] > 0:
        print(f"\nLINE STATISTICS:")
        print(f"  Total lines added: {stats['total_lines_added']:,}")
        print(f"  Average lines added per file: {stats['total_lines_added'] / stats['processed']:.1f}")

        # Show top 10 files by lines added
        results.sort(key=lambda x: x['lines_added'], reverse=True)

        print(f"\nTOP 10 FILES BY LINES ADDED:")
        for i, r in enumerate(results[:10], 1):
            print(f"  {i}. {r['file']}: {r['lines_added']} lines added (1 → {r['new_lines']} lines)")

    if errors:
        print(f"\n\nERRORS ({len(errors)}):")
        for err in errors[:10]:
            print(f"  - {err['file']}: {err['error']}")

    print(f"\nAll files updated in place: {cleaned_dir}")

if __name__ == '__main__':
    main()
