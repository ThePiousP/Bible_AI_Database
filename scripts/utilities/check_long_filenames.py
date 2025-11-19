#!/usr/bin/env python3
"""
Find and report files with long filenames in the cleaned transcripts directory
"""

from pathlib import Path

def main():
    cleaned_dir = Path(r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts_cleaned')

    # Get all files and their name lengths
    files_with_lengths = []
    for file_path in cleaned_dir.glob('*.txt'):
        files_with_lengths.append({
            'path': file_path,
            'name': file_path.name,
            'length': len(file_path.name)
        })

    # Sort by length descending
    files_with_lengths.sort(key=lambda x: x['length'], reverse=True)

    # Windows path limit is 260 characters total
    # Filename limit is typically 255 characters
    print(f"Total files: {len(files_with_lengths)}")
    print(f"\nFiles with names > 200 characters:")
    print("=" * 80)

    long_files = [f for f in files_with_lengths if f['length'] > 200]

    if not long_files:
        print("No files with names longer than 200 characters found!")
    else:
        for f in long_files:
            print(f"\nLength: {f['length']}")
            print(f"Name: {f['name']}")

    print(f"\n\nTop 20 longest filenames:")
    print("=" * 80)
    for i, f in enumerate(files_with_lengths[:20], 1):
        print(f"{i:2}. [{f['length']:3}] {f['name'][:100]}...")

if __name__ == '__main__':
    main()
