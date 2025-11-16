#!/usr/bin/env python3
"""
Extract crossword clues from Concordance.db definition field.

Extracts WORD (from transliteration) and 3 CLUES from the definition field:
- CLUE1: Primary definition/meaning
- CLUE2: Secondary meaning/usage
- CLUE3: Etymology with Strong's reference

Output format: WORD<tab>CLUE1<tab>CLUE2<tab>CLUE3
"""

import sqlite3
import re
from typing import Tuple, Optional, List


class ConcordanceExtractor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.extracted_words = []
        self.problem_entries = []

    def parse_definition(self, strong_num: str, transliteration: str, definition: str) -> Optional[Tuple[str, str, str, str]]:
        """
        Parse definition field into WORD and 3 clues.

        Returns: (WORD, CLUE1, CLUE2, CLUE3) or None if parsing fails
        """
        if not definition or not transliteration:
            self.problem_entries.append({
                'strong_num': strong_num,
                'transliteration': transliteration,
                'definition': definition,
                'reason': 'Missing transliteration or definition'
            })
            return None

        # WORD: Use transliteration as-is (preserving diacritics)
        word = transliteration.strip()

        try:
            # Split on semicolons to separate parts
            parts = definition.split(';')

            if len(parts) < 2:
                # No semicolons - can't parse properly
                self.problem_entries.append({
                    'strong_num': strong_num,
                    'transliteration': transliteration,
                    'definition': definition,
                    'reason': 'Missing semicolons in definition'
                })
                return None

            # CLUE2 (Etymology): Part after first semicolon, before second semicolon
            # This usually contains Strong's references (H#### or G####)
            clue2 = parts[1].strip() if len(parts) > 1 else ""

            # CLUE1: Extract from the definition part (after second semicolon)
            # Split on :— to separate definition from KJV translation
            if len(parts) >= 3:
                definition_part = parts[2].strip()
            else:
                # Only 2 parts, use second part
                definition_part = parts[1].strip()

            # Remove KJV translation part (after :—)
            if ':—' in definition_part:
                definition_part = definition_part.split(':—')[0].strip()
            elif ':-' in definition_part:
                definition_part = definition_part.split(':-')[0].strip()

            # CLUE1 is the definition part
            clue1 = definition_part.strip()

            # CLUE3: Just the Strong's number
            clue3 = strong_num

            # If CLUE2 is empty, log it as a problem
            if not clue2:
                clue2 = f"from Strong's {strong_num}"
                self.problem_entries.append({
                    'strong_num': strong_num,
                    'transliteration': transliteration,
                    'definition': definition,
                    'reason': 'Missing etymology (CLUE2 empty)'
                })

            # Clean up clues (remove trailing periods, extra spaces)
            clue1 = clue1.rstrip('.').strip()
            clue2 = clue2.rstrip('.').strip()
            clue3 = clue3.rstrip('.').strip()

            return (word, clue1, clue2, clue3)

        except Exception as e:
            self.problem_entries.append({
                'strong_num': strong_num,
                'transliteration': transliteration,
                'definition': definition,
                'reason': f'Parsing error: {str(e)}'
            })
            return None

    def extract_from_database(self) -> None:
        """Extract all entries from strongs_lexicon table."""
        print(f"Connecting to database: {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Query all entries from strongs_lexicon
        query = """
            SELECT strong_norm, transliteration, definition
            FROM strongs_lexicon
            WHERE transliteration IS NOT NULL
            AND definition IS NOT NULL
            ORDER BY strong_norm
        """

        print("Extracting entries...")
        cursor.execute(query)

        count = 0
        success_count = 0

        for row in cursor.fetchall():
            strong_num = row[0]
            transliteration = row[1]
            definition = row[2]

            result = self.parse_definition(strong_num, transliteration, definition)

            if result:
                self.extracted_words.append(result)
                success_count += 1

            count += 1
            if count % 1000 == 0:
                print(f"Processed {count} entries... ({success_count} successful)")

        conn.close()

        print(f"\nTotal entries processed: {count}")
        print(f"Successfully extracted: {success_count}")
        print(f"Problem entries: {len(self.problem_entries)}")

    def export_wordlist(self, output_path: str) -> None:
        """Export extracted words to tab-delimited file."""
        print(f"\nExporting {len(self.extracted_words)} entries to {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            for word, clue1, clue2, clue3 in self.extracted_words:
                line = f"{word}\t{clue1}\t{clue2}\t{clue3}\n"
                f.write(line)

        print(f"Export complete: {output_path}")

    def export_problem_entries(self, output_path: str) -> None:
        """Export list of entries that had parsing issues."""
        print(f"\nExporting {len(self.problem_entries)} problem entries to {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Problem Entries Report\n")
            f.write(f"# Total problems: {len(self.problem_entries)}\n\n")

            # Group by reason
            by_reason = {}
            for entry in self.problem_entries:
                reason = entry['reason']
                if reason not in by_reason:
                    by_reason[reason] = []
                by_reason[reason].append(entry)

            # Write summary
            f.write("## Summary by Issue Type\n\n")
            for reason, entries in sorted(by_reason.items()):
                f.write(f"- {reason}: {len(entries)} entries\n")

            f.write("\n" + "="*80 + "\n\n")

            # Write detailed entries
            f.write("## Detailed Problem Entries\n\n")
            for i, entry in enumerate(self.problem_entries, 1):
                f.write(f"{i}. Strong's: {entry['strong_num']}\n")
                f.write(f"   Transliteration: {entry['transliteration']}\n")
                f.write(f"   Definition: {entry['definition'][:200]}\n")
                f.write(f"   Reason: {entry['reason']}\n")
                f.write("\n")

        print(f"Problem entries report complete: {output_path}")

    def print_sample(self, n: int = 10) -> None:
        """Print sample of extracted entries."""
        print(f"\n{'='*80}")
        print(f"SAMPLE OUTPUT (first {n} entries)")
        print(f"{'='*80}\n")

        for i, (word, clue1, clue2, clue3) in enumerate(self.extracted_words[:n], 1):
            # Use ASCII-safe printing for Windows console
            try:
                print(f"{i}. WORD: {word}")
                print(f"   CLUE1: {clue1}")
                print(f"   CLUE2: {clue2}")
                print(f"   CLUE3: {clue3}")
                print()
            except UnicodeEncodeError:
                # Skip entries with problematic characters in console output
                print(f"{i}. [Entry contains special characters - see output file]")
                print()


def main():
    """Main extraction workflow."""
    import sys
    import os

    # Default path
    db_path = r'D:\Project_PP\projects\bible\data\concordance.db'

    # Allow command-line override
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        print("\nUsage:")
        print(f"  python {sys.argv[0]} [/path/to/concordance.db]")
        sys.exit(1)

    # Run extraction
    extractor = ConcordanceExtractor(db_path)
    extractor.extract_from_database()

    # Show sample
    extractor.print_sample(10)

    # Export results
    output_file = 'concordance_crossword_clues.txt'
    problem_file = 'concordance_problem_entries.txt'

    extractor.export_wordlist(output_file)
    extractor.export_problem_entries(problem_file)

    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    print(f"\nFiles created:")
    print(f"  1. {output_file} - Ready for crossword puzzle use")
    print(f"  2. {problem_file} - Entries needing review/manual processing")
    print("\nNext steps:")
    print("  1. Review sample output above")
    print("  2. Check problem entries file for issues")
    print("  3. Process with AI to clean up diacritics (as planned)")
    print("  4. Import into your crossword game!")


if __name__ == "__main__":
    main()
