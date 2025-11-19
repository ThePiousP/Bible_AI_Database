#!/usr/bin/env python3
"""
Comprehensive check of all transcript files for line counts
"""

from pathlib import Path

def main():
    cleaned_dir = Path(r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts_cleaned')
    all_files = list(cleaned_dir.glob('*.txt'))

    single_line = []
    very_short = []  # 2-10 lines
    short = []  # 11-25 lines
    good = []  # 26+ lines

    for file_path in all_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            line_count = text.count('\n') + 1
            char_count = len(text)
            word_count = len(text.split())

            file_info = {
                'name': file_path.name,
                'path': file_path,
                'lines': line_count,
                'chars': char_count,
                'words': word_count
            }

            if line_count == 1:
                single_line.append(file_info)
            elif line_count <= 10:
                very_short.append(file_info)
            elif line_count <= 25:
                short.append(file_info)
            else:
                good.append(file_info)

        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    # Print comprehensive report
    print("COMPREHENSIVE LINE COUNT CHECK")
    print("=" * 100)
    print(f"Total files checked: {len(all_files)}\n")

    print(f"BREAKDOWN BY LINE COUNT:")
    print(f"  Single-line (1 line):       {len(single_line):4} ({len(single_line)/len(all_files)*100:5.1f}%)")
    print(f"  Very short (2-10 lines):    {len(very_short):4} ({len(very_short)/len(all_files)*100:5.1f}%)")
    print(f"  Short (11-25 lines):        {len(short):4} ({len(short)/len(all_files)*100:5.1f}%)")
    print(f"  Good (26+ lines):           {len(good):4} ({len(good)/len(all_files)*100:5.1f}%)")

    # Single-line files
    if single_line:
        print(f"\n\nALL SINGLE-LINE FILES ({len(single_line)}):")
        print("=" * 100)
        single_line.sort(key=lambda x: x['chars'], reverse=True)
        for i, f in enumerate(single_line, 1):
            print(f"{i:2}. {f['name'][:70]:70} | {f['chars']:6,} chars | {f['words']:5,} words")

        # Show a sample from one
        print(f"\n\nSAMPLE FROM: {single_line[0]['name']}")
        print("-" * 100)
        with open(single_line[0]['path'], 'r', encoding='utf-8') as file:
            sample = file.read()[:300]
        print(sample + "...")

    # Very short files
    if very_short:
        print(f"\n\nVERY SHORT FILES (2-10 lines) ({len(very_short)}):")
        print("=" * 100)
        very_short.sort(key=lambda x: x['lines'])
        for i, f in enumerate(very_short, 1):
            print(f"{i:2}. {f['name'][:60]:60} | {f['lines']:2} lines | {f['chars']:6,} chars")

    # Short files
    if short:
        print(f"\n\nSHORT FILES (11-25 lines) ({len(short)}):")
        print("=" * 100)
        short.sort(key=lambda x: x['lines'])
        for i, f in enumerate(short[:20], 1):
            print(f"{i:2}. {f['name'][:60]:60} | {f['lines']:2} lines | {f['chars']:6,} chars")
        if len(short) > 20:
            print(f"... and {len(short) - 20} more")

    print(f"\n\n{'='*100}")
    print(f"RECOMMENDATION:")
    print(f"{'='*100}")

    problem_files = len(single_line) + len(very_short)
    if problem_files > 0:
        print(f"Found {problem_files} files with 10 or fewer lines that may need attention.")
        print(f"This represents {problem_files/len(all_files)*100:.1f}% of all files.")
    else:
        print(f"All files look good! No single-line or very short files found.")

if __name__ == '__main__':
    main()
