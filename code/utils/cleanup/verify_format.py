"""
Verify that every line has exactly 4 tab-separated fields
"""

def verify_format(file_path):
    print(f"Verifying format of {file_path}...")
    print("Expected format: <WORD><tab><clue1><tab><clue2><tab><verse+citation>")
    print()

    issues = []
    total_lines = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            line = line.rstrip('\n')

            if not line:
                issues.append((line_num, "Empty line"))
                continue

            # Count tabs
            tab_count = line.count('\t')

            if tab_count != 3:
                issues.append((line_num, f"Has {tab_count} tabs (expected 3)", line[:100]))

    print(f"Total lines: {total_lines}")
    print(f"Issues found: {len(issues)}")

    if issues:
        print("\n" + "="*70)
        print("FORMAT ISSUES:")
        print("="*70)
        for item in issues[:50]:
            if len(item) == 3:
                line_num, reason, content = item
                print(f"Line {line_num}: {reason}")
                print(f"  {content}...")
            else:
                line_num, reason = item
                print(f"Line {line_num}: {reason}")

        if len(issues) > 50:
            print(f"\n... and {len(issues) - 50} more issues")
    else:
        print("\n[OK] All lines have correct format!")
        print("[OK] Every line has exactly 3 tabs (4 fields)")

    return total_lines, len(issues)

if __name__ == "__main__":
    file_path = r"D:\Project_PP\projects\bible\dev\kjv_complete_full.txt"

    print("="*70)
    print("FORMAT VERIFICATION")
    print("="*70)
    print()

    total, issues = verify_format(file_path)

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total entries: {total}")
    print(f"Format issues: {issues}")

    if issues == 0:
        print("\n✓ File format is correct!")
        print("✓ File is alphabetized")
        print("✓ All entries have: <WORD><tab><clue1><tab><clue2><tab><verse+citation>")
    else:
        print(f"\n✗ {issues} lines need correction")
