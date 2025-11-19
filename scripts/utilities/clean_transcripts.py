#!/usr/bin/env python3
"""
Clean sermon transcripts by removing radio show boilerplate

Based on analysis of 60 random samples:
- 26.7% have song lyrics opening
- 16.7% have "Welcome to The Word for Today"
- 10% have "Here's Pastor Chuck" intro
- 85% have promotional content
- 31.7% have contact information
- 25% have "We'll return" phrase
- 26.7% have "sponsored by" phrase
- 18.3% end with "Amen" (but 55% contain "Amen" somewhere)
"""

import re
from pathlib import Path
from typing import Tuple, Optional

class TranscriptCleaner:

    def __init__(self):
        # Opening patterns to remove (in order of priority)
        self.opening_patterns = [
            # Song lyrics: "Oh let/Oh, let the Son of God enfold you..." - matches both "hold" and "mold" variants
            # Stops at either "Here's/here is Pastor Chuck" or at the period after "make you whole"
            r'^Oh[,]?\s+let the Son of God enfold you.*?(?:make you whole\.?\s+)',

            # Welcome message - everything up to and including "Here's Pastor Chuck" or "here is Pastor Chuck"
            r'^Welcome to The Word for Today.*?(?:Here\'s|here is) Pastor Chuck\.?\s*',

            # "And now with/And now, with today's message/lesson/study" followed by "Here's/here is Pastor Chuck"
            # (must be near start, within first 1000 chars)
            r'^.{0,1000}?And now[,]?\s+with today\'s (?:message|lesson|study)[.,]?\s*(?:here\'s|here is) Pastor Chuck(?:\s+Smith)?[.,]?\s*',

            # Just "Here's Pastor Chuck" at the very beginning (within first 100 chars)
            r'^.{0,100}?(?:Here\'s|here is) Pastor Chuck\.?\s*',
        ]

        # Closing patterns to remove (find earliest match)
        self.closing_patterns = [
            # "We'll return with more..." - most common
            r'We\'ll return with more.*$',

            # "Pastor Chuck will return with a few closing comments..."
            r'Pastor Chuck will return with a few closing comments.*$',

            # "And now once again here's Pastor Chuck with today's closing comments"
            r'And now once again here\'s Pastor Chuck with today\'s closing comments.*$',

            # Direct promotional content
            r'Have you laid hold of what God has called you to do\?.*$',

            # Contact info blocks
            r'(?:If you wish to call|Simply write or call|You can also subscribe).*$',

            # "This program" sponsor message - can appear after Amen
            r'(?:Amen\s+)?This program (?:has been )?(?:is )?sponsored by.*$',
        ]

    def remove_opening_boilerplate(self, text: str) -> Tuple[str, int]:
        """
        Remove opening boilerplate (song, welcome, intro)
        Returns: (cleaned_text, chars_removed)
        """
        original_length = len(text)

        for pattern in self.opening_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                text = text[match.end():]
                break

        chars_removed = original_length - len(text)
        return text.lstrip(), chars_removed

    def remove_closing_boilerplate(self, text: str) -> Tuple[str, int]:
        """
        Remove closing boilerplate (promotional, contact, sponsor)
        Returns: (cleaned_text, chars_removed)
        """
        original_length = len(text)

        # Find earliest closing pattern match
        earliest_pos = len(text)
        earliest_pattern = None

        for pattern in self.closing_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match and match.start() < earliest_pos:
                earliest_pos = match.start()
                earliest_pattern = pattern

        if earliest_pattern:
            text = text[:earliest_pos]

        chars_removed = original_length - len(text)
        return text.rstrip(), chars_removed

    def clean_transcript(self, text: str) -> dict:
        """
        Clean a transcript and return results

        Returns:
            dict with:
                - cleaned_text: the cleaned transcript
                - opening_removed: chars removed from opening
                - closing_removed: chars removed from closing
                - original_length: original text length
                - cleaned_length: cleaned text length
        """
        original_length = len(text)

        # Remove opening boilerplate
        text, opening_removed = self.remove_opening_boilerplate(text)

        # Remove closing boilerplate
        text, closing_removed = self.remove_closing_boilerplate(text)

        # Clean up extra whitespace
        text = text.strip()

        return {
            'cleaned_text': text,
            'opening_removed': opening_removed,
            'closing_removed': closing_removed,
            'original_length': original_length,
            'cleaned_length': len(text),
            'total_removed': opening_removed + closing_removed,
            'percent_removed': ((opening_removed + closing_removed) / original_length * 100) if original_length > 0 else 0
        }

    def clean_file(self, file_path: Path, output_dir: Optional[Path] = None, dry_run: bool = False) -> dict:
        """
        Clean a transcript file

        Args:
            file_path: Path to transcript file
            output_dir: Directory to save cleaned file (if None, overwrites original)
            dry_run: If True, don't write files, just return results

        Returns:
            dict with cleaning results and file info
        """
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_text = f.read()

            # Clean the text
            result = self.clean_transcript(original_text)

            # Add file info
            result['file'] = file_path.name
            result['file_path'] = str(file_path)

            # Write cleaned file if not dry run
            if not dry_run:
                if output_dir:
                    output_file = output_dir / file_path.name
                else:
                    output_file = file_path

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result['cleaned_text'])

                result['output_file'] = str(output_file)

            return result

        except Exception as e:
            return {
                'file': file_path.name,
                'file_path': str(file_path),
                'error': str(e)
            }


def main():
    """Test the cleaner on a few sample files"""
    import random

    cleaner = TranscriptCleaner()

    # Get transcript directory
    transcript_dir = Path(r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts')

    # Get all files
    all_files = list(transcript_dir.glob('*.txt'))
    print(f"Found {len(all_files)} transcript files")

    # Sample 10 random files for testing
    sample_files = random.sample(all_files, min(10, len(all_files)))

    print(f"\nTesting cleaner on {len(sample_files)} random files (DRY RUN)...\n")
    print("=" * 80)

    results = []
    for i, file_path in enumerate(sample_files, 1):
        print(f"\n[{i}/{len(sample_files)}] {file_path.name}")
        result = cleaner.clean_file(file_path, dry_run=True)

        if 'error' in result:
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  Original length: {result['original_length']:,} chars")
            print(f"  Opening removed: {result['opening_removed']:,} chars")
            print(f"  Closing removed: {result['closing_removed']:,} chars")
            print(f"  Cleaned length:  {result['cleaned_length']:,} chars")
            print(f"  Total removed:   {result['total_removed']:,} chars ({result['percent_removed']:.1f}%)")

            # Show first 100 chars of cleaned text
            preview = result['cleaned_text'][:100]
            print(f"  Preview: {preview}...")

        results.append(result)

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    valid_results = [r for r in results if 'error' not in r]

    if valid_results:
        avg_opening = sum(r['opening_removed'] for r in valid_results) / len(valid_results)
        avg_closing = sum(r['closing_removed'] for r in valid_results) / len(valid_results)
        avg_total = sum(r['total_removed'] for r in valid_results) / len(valid_results)
        avg_percent = sum(r['percent_removed'] for r in valid_results) / len(valid_results)

        print(f"\nFiles processed: {len(valid_results)}")
        print(f"Average opening removed: {avg_opening:,.0f} chars")
        print(f"Average closing removed: {avg_closing:,.0f} chars")
        print(f"Average total removed: {avg_total:,.0f} chars ({avg_percent:.1f}%)")

        files_with_opening = sum(1 for r in valid_results if r['opening_removed'] > 0)
        files_with_closing = sum(1 for r in valid_results if r['closing_removed'] > 0)

        print(f"\nFiles with opening boilerplate: {files_with_opening}/{len(valid_results)} ({files_with_opening/len(valid_results)*100:.1f}%)")
        print(f"Files with closing boilerplate: {files_with_closing}/{len(valid_results)} ({files_with_closing/len(valid_results)*100:.1f}%)")


if __name__ == '__main__':
    main()
