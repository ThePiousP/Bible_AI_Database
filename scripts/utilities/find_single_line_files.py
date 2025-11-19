#!/usr/bin/env python3
"""
Find transcript files that only have one line (missing line breaks)
"""

from pathlib import Path

def main():
    cleaned_dir = Path(r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts_cleaned')

    # Get all transcript files
    all_files = list(cleaned_dir.glob('*.txt'))

    print(f"CHECKING FOR SINGLE-LINE FILES")
    print("=" * 80)
    print(f"Total files: {len(all_files)}\n")

    single_line_files = []
    few_line_files = []  # Files with 1-5 lines

    for file_path in all_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            line_count = text.count('\n') + 1
            char_count = len(text)

            if line_count == 1:
                single_line_files.append({
                    'name': file_path.name,
                    'path': file_path,
                    'chars': char_count,
                    'lines': line_count
                })
            elif line_count <= 5:
                few_line_files.append({
                    'name': file_path.name,
                    'path': file_path,
                    'chars': char_count,
                    'lines': line_count
                })

        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    # Report results
    print(f"FILES WITH EXACTLY 1 LINE: {len(single_line_files)}")
    print("=" * 80)

    if single_line_files:
        # Sort by character count (descending)
        single_line_files.sort(key=lambda x: x['chars'], reverse=True)

        for i, f in enumerate(single_line_files[:20], 1):
            print(f"\n{i}. {f['name']}")
            print(f"   Characters: {f['chars']:,}")
            print(f"   Lines: {f['lines']}")

        if len(single_line_files) > 20:
            print(f"\n... and {len(single_line_files) - 20} more single-line files")

        # Show a sample of the first one
        print(f"\n" + "=" * 80)
        print("SAMPLE FROM FIRST FILE:")
        print("=" * 80)
        with open(single_line_files[0]['path'], 'r', encoding='utf-8') as f:
            sample = f.read()[:500]
        print(sample)
    else:
        print("No single-line files found!")

    print(f"\n\nFILES WITH 2-5 LINES: {len(few_line_files)}")
    print("=" * 80)

    if few_line_files:
        few_line_files.sort(key=lambda x: x['chars'], reverse=True)

        for i, f in enumerate(few_line_files[:10], 1):
            print(f"{i}. {f['name']} - {f['lines']} lines, {f['chars']:,} chars")

    print(f"\n\nSUMMARY:")
    print(f"  Total files: {len(all_files)}")
    print(f"  Single-line files: {len(single_line_files)} ({len(single_line_files)/len(all_files)*100:.1f}%)")
    print(f"  Files with 2-5 lines: {len(few_line_files)} ({len(few_line_files)/len(all_files)*100:.1f}%)")
    print(f"  Files with 6+ lines: {len(all_files) - len(single_line_files) - len(few_line_files)} ({(len(all_files) - len(single_line_files) - len(few_line_files))/len(all_files)*100:.1f}%)")

if __name__ == '__main__':
    main()
