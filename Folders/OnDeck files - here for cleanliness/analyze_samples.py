#!/usr/bin/env python3
"""
Analyze 60 random sermon transcript samples to identify radio block patterns
"""

import random
import re
from pathlib import Path
from collections import Counter

def analyze_transcript(file_path):
    """Analyze a single transcript for patterns"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        results = {
            'file': file_path.name,
            'total_lines': content.count('\n') + 1,
            'word_count': len(content.split()),
            'has_song_lyrics': bool(re.search(r'enfold you|Spirit like a dove|make you whole', content, re.IGNORECASE)),
            'has_welcome': bool(re.search(r'Welcome to The Word for Today', content)),
            'has_pastor_chuck_intro': bool(re.search(r'Here\'s Pastor Chuck', content)),
            'has_closing_contact': bool(re.search(r'1-800-272-WORD|TheWordForToday\.org|P\.O\. Box 8000', content)),
            'has_closing_return': bool(re.search(r'We\'ll return with more', content)),
            'has_promotional': bool(re.search(r'order|subscribe|podcast|email subscription|DVD|MP3', content, re.IGNORECASE)),
            'has_sponsored_by': bool(re.search(r'This program (?:has been )?sponsored by', content)),
            'ends_with_amen': bool(re.search(r'Amen\.?\s*$', content.strip(), re.IGNORECASE)),
            'has_amen': bool(re.search(r'\bAmen\b', content, re.IGNORECASE)),
            'amen_count': len(re.findall(r'\bAmen\b', content, re.IGNORECASE)),
        }

        # Find opening boilerplate
        opening_match = re.search(r'^(.*?(?:Here\'s Pastor Chuck|And now with today\'s (?:message|lesson)))', content, re.DOTALL)
        if opening_match:
            results['opening_chars'] = len(opening_match.group(1))
        else:
            results['opening_chars'] = 0

        # Find closing boilerplate starting points
        closing_patterns = [
            r'We\'ll return with more',
            r'While you\'re there we encourage',
            r'If you wish to call our toll-free',
            r'Have you laid hold of what God',
            r'This program (?:has been )?sponsored by',
            r'And now once again here\'s Pastor Chuck with today\'s closing comments',
            r'Pastor Chuck will return with a few closing comments',
        ]

        earliest_closing = len(content)
        closing_found = None
        for pattern in closing_patterns:
            match = re.search(pattern, content)
            if match and match.start() < earliest_closing:
                earliest_closing = match.start()
                closing_found = pattern

        if closing_found:
            results['closing_start_chars'] = earliest_closing
            results['closing_chars'] = len(content) - earliest_closing
            results['closing_pattern'] = closing_found
        else:
            results['closing_start_chars'] = None
            results['closing_chars'] = 0
            results['closing_pattern'] = None

        # Extract first 200 and last 200 characters for manual inspection
        results['first_200'] = content[:200]
        results['last_200'] = content[-200:]

        return results

    except Exception as e:
        return {'file': file_path.name, 'error': str(e)}

def main():
    """Process 60 random sermon files"""
    transcript_dir = Path(r'D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts')

    # Get all transcript files
    all_files = list(transcript_dir.rglob('*.txt'))
    print(f"Found {len(all_files)} total transcript files")

    # Sample 60 random files
    sample_size = min(60, len(all_files))
    sample_files = random.sample(all_files, sample_size)

    print(f"\nAnalyzing {sample_size} random transcripts...\n")

    results = []
    for i, file_path in enumerate(sample_files, 1):
        print(f"[{i}/{sample_size}] Analyzing {file_path.name}...")
        result = analyze_transcript(file_path)
        results.append(result)

    # Compile statistics
    print("\n" + "="*80)
    print("ANALYSIS RESULTS")
    print("="*80)

    stats = {
        'has_song_lyrics': sum(1 for r in results if r.get('has_song_lyrics', False)),
        'has_welcome': sum(1 for r in results if r.get('has_welcome', False)),
        'has_pastor_chuck_intro': sum(1 for r in results if r.get('has_pastor_chuck_intro', False)),
        'has_closing_contact': sum(1 for r in results if r.get('has_closing_contact', False)),
        'has_closing_return': sum(1 for r in results if r.get('has_closing_return', False)),
        'has_promotional': sum(1 for r in results if r.get('has_promotional', False)),
        'has_sponsored_by': sum(1 for r in results if r.get('has_sponsored_by', False)),
        'ends_with_amen': sum(1 for r in results if r.get('ends_with_amen', False)),
        'has_amen': sum(1 for r in results if r.get('has_amen', False)),
    }

    print(f"\nOPENING PATTERNS:")
    print(f"  Song lyrics found: {stats['has_song_lyrics']}/{sample_size} ({stats['has_song_lyrics']/sample_size*100:.1f}%)")
    print(f"  'Welcome to The Word for Today': {stats['has_welcome']}/{sample_size} ({stats['has_welcome']/sample_size*100:.1f}%)")
    print(f"  'Here's Pastor Chuck' intro: {stats['has_pastor_chuck_intro']}/{sample_size} ({stats['has_pastor_chuck_intro']/sample_size*100:.1f}%)")

    print(f"\nCLOSING PATTERNS:")
    print(f"  Contact information: {stats['has_closing_contact']}/{sample_size} ({stats['has_closing_contact']/sample_size*100:.1f}%)")
    print(f"  'We'll return' phrase: {stats['has_closing_return']}/{sample_size} ({stats['has_closing_return']/sample_size*100:.1f}%)")
    print(f"  Promotional content: {stats['has_promotional']}/{sample_size} ({stats['has_promotional']/sample_size*100:.1f}%)")
    print(f"  'Sponsored by' phrase: {stats['has_sponsored_by']}/{sample_size} ({stats['has_sponsored_by']/sample_size*100:.1f}%)")

    print(f"\nAMEN ANALYSIS:")
    print(f"  Contains 'Amen': {stats['has_amen']}/{sample_size} ({stats['has_amen']/sample_size*100:.1f}%)")
    print(f"  Ends with 'Amen': {stats['ends_with_amen']}/{sample_size} ({stats['ends_with_amen']/sample_size*100:.1f}%)")

    # Amen count distribution
    amen_counts = [r.get('amen_count', 0) for r in results]
    print(f"  Total Amen occurrences: {sum(amen_counts)}")
    print(f"  Average per transcript: {sum(amen_counts)/len(amen_counts):.1f}")
    print(f"  Max Amen in one transcript: {max(amen_counts)}")

    # Closing pattern distribution
    closing_patterns = [r.get('closing_pattern') for r in results if r.get('closing_pattern')]
    pattern_counts = Counter(closing_patterns)
    print(f"\nCLOSING PATTERN FREQUENCY:")
    for pattern, count in pattern_counts.most_common():
        print(f"  {pattern[:50]}: {count}")

    # Average boilerplate size
    opening_sizes = [r.get('opening_chars', 0) for r in results if r.get('opening_chars', 0) > 0]
    closing_sizes = [r.get('closing_chars', 0) for r in results if r.get('closing_chars', 0) > 0]

    if opening_sizes:
        print(f"\nOPENING BOILERPLATE SIZE:")
        print(f"  Average: {sum(opening_sizes)/len(opening_sizes):.0f} characters")
        print(f"  Max: {max(opening_sizes)} characters")

    if closing_sizes:
        print(f"\nCLOSING BOILERPLATE SIZE:")
        print(f"  Average: {sum(closing_sizes)/len(closing_sizes):.0f} characters")
        print(f"  Max: {max(closing_sizes)} characters")

    # Show sample openings and closings
    print(f"\n" + "="*80)
    print("SAMPLE OPENINGS (first 200 chars)")
    print("="*80)
    for i, r in enumerate(results[:5], 1):
        print(f"\n[{i}] {r['file']}")
        print(f"{r.get('first_200', 'N/A')}")

    print(f"\n" + "="*80)
    print("SAMPLE CLOSINGS (last 200 chars)")
    print("="*80)
    for i, r in enumerate(results[:5], 1):
        print(f"\n[{i}] {r['file']}")
        print(f"{r.get('last_200', 'N/A')}")

    # Save detailed results
    output_file = Path(r'D:\Project_PP\projects\bible\sample_analysis_results.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("DETAILED ANALYSIS RESULTS\n")
        f.write("="*80 + "\n\n")

        for r in results:
            f.write(f"File: {r['file']}\n")
            f.write(f"  Word count: {r.get('word_count', 'N/A')}\n")
            f.write(f"  Total lines: {r.get('total_lines', 'N/A')}\n")
            f.write(f"  Has song lyrics: {r.get('has_song_lyrics', False)}\n")
            f.write(f"  Has welcome: {r.get('has_welcome', False)}\n")
            f.write(f"  Has Pastor Chuck intro: {r.get('has_pastor_chuck_intro', False)}\n")
            f.write(f"  Has closing contact: {r.get('has_closing_contact', False)}\n")
            f.write(f"  Has closing return: {r.get('has_closing_return', False)}\n")
            f.write(f"  Has promotional: {r.get('has_promotional', False)}\n")
            f.write(f"  Has sponsored by: {r.get('has_sponsored_by', False)}\n")
            f.write(f"  Ends with Amen: {r.get('ends_with_amen', False)}\n")
            f.write(f"  Amen count: {r.get('amen_count', 0)}\n")
            f.write(f"  Opening chars: {r.get('opening_chars', 0)}\n")
            f.write(f"  Closing chars: {r.get('closing_chars', 0)}\n")
            f.write(f"  Closing pattern: {r.get('closing_pattern', 'None')}\n")
            f.write(f"\n  FIRST 200 CHARS:\n  {r.get('first_200', 'N/A')}\n")
            f.write(f"\n  LAST 200 CHARS:\n  {r.get('last_200', 'N/A')}\n")
            f.write("\n" + "-"*80 + "\n\n")

    print(f"\n\nDetailed results saved to: {output_file}")

if __name__ == '__main__':
    main()
