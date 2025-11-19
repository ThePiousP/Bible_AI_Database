#!/usr/bin/env python3
"""
Clean ALL sermon transcripts by removing radio show boilerplate

This script processes all transcript files in the transcripts directory
and saves cleaned versions to a new directory.
"""

from pathlib import Path
from clean_transcripts import TranscriptCleaner
import time

def main():
    """Clean all transcript files"""

    cleaner = TranscriptCleaner()

    # Directories
    transcript_dir = Path(r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts')
    output_dir = Path(r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts_cleaned')

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all transcript files
    all_files = list(transcript_dir.glob('*.txt'))
    total_files = len(all_files)

    print(f"Found {total_files} transcript files")
    print(f"Output directory: {output_dir}")
    print(f"\nStarting cleaning process...\n")
    print("=" * 80)

    # Statistics
    stats = {
        'processed': 0,
        'errors': 0,
        'with_opening': 0,
        'with_closing': 0,
        'total_original_chars': 0,
        'total_removed_chars': 0,
    }

    errors = []
    start_time = time.time()

    # Process each file
    for i, file_path in enumerate(all_files, 1):
        try:
            # Clean the file
            result = cleaner.clean_file(file_path, output_dir=output_dir, dry_run=False)

            if 'error' in result:
                stats['errors'] += 1
                errors.append(result)
                print(f"[{i}/{total_files}] ERROR: {file_path.name}")
                print(f"            {result['error']}")
            else:
                stats['processed'] += 1
                stats['total_original_chars'] += result['original_length']
                stats['total_removed_chars'] += result['total_removed']

                if result['opening_removed'] > 0:
                    stats['with_opening'] += 1
                if result['closing_removed'] > 0:
                    stats['with_closing'] += 1

                # Print progress every 50 files or if significant cleaning occurred
                if i % 50 == 0 or result['percent_removed'] > 10:
                    print(f"[{i}/{total_files}] OK {file_path.name}")
                    if result['total_removed'] > 0:
                        print(f"            Removed: {result['total_removed']:,} chars ({result['percent_removed']:.1f}%)")

        except Exception as e:
            stats['errors'] += 1
            errors.append({'file': file_path.name, 'error': str(e)})
            print(f"[{i}/{total_files}] ERROR: {file_path.name}")
            print(f"            {str(e)}")

    elapsed_time = time.time() - start_time

    # Print summary
    print("\n" + "=" * 80)
    print("CLEANING COMPLETE")
    print("=" * 80)

    print(f"\nTotal files found: {total_files}")
    print(f"Successfully processed: {stats['processed']}")
    print(f"Errors: {stats['errors']}")
    print(f"Time elapsed: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")

    if stats['processed'] > 0:
        print(f"\nCLEANING STATISTICS:")
        print(f"  Files with opening boilerplate: {stats['with_opening']} ({stats['with_opening']/stats['processed']*100:.1f}%)")
        print(f"  Files with closing boilerplate: {stats['with_closing']} ({stats['with_closing']/stats['processed']*100:.1f}%)")

        avg_removed = stats['total_removed_chars'] / stats['processed']
        avg_percent = (stats['total_removed_chars'] / stats['total_original_chars'] * 100) if stats['total_original_chars'] > 0 else 0

        print(f"\n  Total original content: {stats['total_original_chars']:,} characters")
        print(f"  Total removed: {stats['total_removed_chars']:,} characters")
        print(f"  Average removed per file: {avg_removed:,.0f} characters ({avg_percent:.1f}%)")

    if errors:
        print(f"\n\nERRORS ({len(errors)}):")
        for err in errors[:10]:  # Show first 10 errors
            print(f"  - {err['file']}: {err['error']}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")

    print(f"\nCleaned transcripts saved to: {output_dir}")
    print("\nNext steps:")
    print("  1. Review a few cleaned files to verify quality")
    print("  2. Compare original vs cleaned for accuracy")
    print("  3. Use cleaned transcripts for database import")

if __name__ == '__main__':
    main()
