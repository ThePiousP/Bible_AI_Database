#!/usr/bin/env python3
"""
Remove all empty lines from cleaned sermon transcript files
"""

from pathlib import Path
import time

def remove_empty_lines(text):
    """
    Remove all empty lines (lines with only whitespace)
    Returns: (cleaned_text, lines_removed)
    """
    lines = text.split('\n')
    original_count = len(lines)

    # Keep only non-empty lines (lines with actual content)
    non_empty_lines = [line for line in lines if line.strip()]

    cleaned_text = '\n'.join(non_empty_lines)
    lines_removed = original_count - len(non_empty_lines)

    return cleaned_text, lines_removed

def process_file(file_path):
    """Process a single file to remove empty lines"""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            original_text = f.read()

        original_lines = original_text.count('\n') + 1

        # Remove empty lines
        cleaned_text, lines_removed = remove_empty_lines(original_text)

        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)

        return {
            'file': file_path.name,
            'original_lines': original_lines,
            'lines_removed': lines_removed,
            'final_lines': original_lines - lines_removed,
            'success': True
        }

    except Exception as e:
        return {
            'file': file_path.name,
            'error': str(e),
            'success': False
        }

def main():
    """Process all transcript files"""

    cleaned_dir = Path(r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts_cleaned')

    # Get all transcript files
    all_files = list(cleaned_dir.glob('*.txt'))
    total_files = len(all_files)

    print(f"REMOVING EMPTY LINES FROM TRANSCRIPT FILES")
    print("=" * 80)
    print(f"Directory: {cleaned_dir}")
    print(f"Files to process: {total_files}")
    print("\nProcessing...\n")

    # Statistics
    stats = {
        'processed': 0,
        'errors': 0,
        'total_lines_removed': 0,
        'total_original_lines': 0,
        'total_final_lines': 0,
    }

    errors = []
    start_time = time.time()

    # Process each file
    for i, file_path in enumerate(all_files, 1):
        result = process_file(file_path)

        if result['success']:
            stats['processed'] += 1
            stats['total_lines_removed'] += result['lines_removed']
            stats['total_original_lines'] += result['original_lines']
            stats['total_final_lines'] += result['final_lines']

            # Print progress every 100 files
            if i % 100 == 0:
                print(f"[{i}/{total_files}] Processed {stats['processed']} files, removed {stats['total_lines_removed']:,} empty lines")
        else:
            stats['errors'] += 1
            errors.append(result)
            print(f"[{i}/{total_files}] ERROR: {result['file']} - {result['error']}")

    elapsed_time = time.time() - start_time

    # Print summary
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)

    print(f"\nTotal files: {total_files}")
    print(f"Successfully processed: {stats['processed']}")
    print(f"Errors: {stats['errors']}")
    print(f"Time elapsed: {elapsed_time:.1f} seconds")

    if stats['processed'] > 0:
        print(f"\nLINE STATISTICS:")
        print(f"  Total original lines: {stats['total_original_lines']:,}")
        print(f"  Total empty lines removed: {stats['total_lines_removed']:,}")
        print(f"  Total final lines: {stats['total_final_lines']:,}")

        avg_lines_removed = stats['total_lines_removed'] / stats['processed']
        percent_removed = (stats['total_lines_removed'] / stats['total_original_lines'] * 100) if stats['total_original_lines'] > 0 else 0

        print(f"\n  Average empty lines per file: {avg_lines_removed:.1f}")
        print(f"  Percentage of lines removed: {percent_removed:.1f}%")

    if errors:
        print(f"\n\nERRORS ({len(errors)}):")
        for err in errors[:10]:
            print(f"  - {err['file']}: {err['error']}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")

    print(f"\nAll files updated in place: {cleaned_dir}")

if __name__ == '__main__':
    main()
