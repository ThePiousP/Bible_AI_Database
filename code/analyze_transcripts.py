#!/usr/bin/env python3
"""
Analyze transcript formatting issues
Sample 25 files and report on:
- Line count
- Has proper paragraphs
- Single-line format
- Opening boilerplate patterns
- Closing boilerplate patterns
- Word count
"""

import re
from pathlib import Path
from collections import Counter

def analyze_file(file_path):
    """Analyze a single transcript file"""
    text = file_path.read_text(encoding='utf-8')
    lines = text.split('\n')

    # Basic stats
    stats = {
        'filename': file_path.name,
        'total_lines': len(lines),
        'non_empty_lines': len([l for l in lines if l.strip()]),
        'word_count': len(text.split()),
        'char_count': len(text),
    }

    # Check formatting
    stats['single_line'] = len(lines) < 10
    stats['has_paragraphs'] = '\n\n' in text

    # Check for boilerplate patterns
    stats['has_song_lyrics'] = 'let the Son of God enfold you' in text or 'make you whole' in text
    stats['has_radio_intro'] = 'Welcome to The Word for Today' in text
    stats['has_pastor_intro'] = "Here's Pastor Chuck" in text or "Here's pastor Chuck" in text.lower()
    stats['has_closing_contact'] = '1-800-272-WORD' in text or 'TheWordForToday.org' in text
    stats['has_closing_promo'] = 'Women\'s Conference' in text or 'special surprise' in text
    stats['ends_with_amen'] = text.strip().endswith('Amen.') or text.strip().endswith('amen.')

    # Get first 200 chars and last 200 chars
    stats['start'] = text[:200].replace('\n', ' ')
    stats['end'] = text[-200:].replace('\n', ' ')

    return stats

def main():
    transcript_dir = Path(r"D:\Project_PP\projects\bible\output\sermons\chuck_smith\transcripts")

    # Sample files
    sample_files = [
        "Deuteronomy_11_271Blessings_and_CursesChoicesDEU_11_26Chuck_Smith_emphasizes_the_importance_of_makin_qAQh67bO.txt",
        "Isaiah_19_11_-_Part_23._mwgJRLY5.txt",
        "The_More_Sure_Word1._RXpBHMJU.txt",
        "The_Fourth_Man1._1lFxkFug.txt",
        "Psalms_81-901._z5cqRcp1.txt",
        "Acts_26-271._b4rEEUlF.txt",
        "Facing_Afflictions1._Jav5MKsz.txt",
        "Revelation_161._XnbT9r1l.txt",
        "Judges_15-161._qwSjOPmG.txt",
        "Revelation_8-91._WNRiFS-Y.txt",
        "Israel's_Rapid_Multiplication52225_05IsraelEXO_1_1EXO_2_15In_this_sermon,_Pastor_Chuck_Smith_begins_fNOUb11p.txt",
        "The_Deed_to_the_Land1._3Cg2Kc8g.txt",
        "God_Knows_Best1._L0X0Efr8.txt",
        "Proverbs_11-151._2etc578V.txt",
        "A_Plea_for_Relief_Part_11._vInMWaJB.txt",
        "Knowing_His_Perfect_Will_-_Part_12._-SvGO5JR.txt",
        "The_End_of_the_Line2._XL33RFnN.txt",
        "I_Samuel_4_31Faith_vs._RitualTrue_Worship1SA_4_3MAT_15_8JHN_14_6ROM_10_9EPH_2_8COL_2_82TI_3_5HEB_10_wmvC-0rf.txt",
        "1_Corinthians_122._BM1A7twF.txt",
        "2_Corinthians_61._Nx-AYVtb.txt",
        "Matthew_51._xh7owKs8.txt",
        "Exodus_16-181._B6uaAmEz.txt",
        "Prayer,_Monolog_or_Dialog_1._OR3cM2TZ.txt",
        "Isaiah_17_1_-_Part_34._rKwpdsat.txt",
        "The_Folly_of_the_World's_Philosophy2._yo7xk5Mc.txt",
    ]

    results = []
    for filename in sample_files:
        file_path = transcript_dir / filename
        if file_path.exists():
            stats = analyze_file(file_path)
            results.append(stats)
        else:
            print(f"File not found: {filename}")

    # Summary statistics
    print(f"\n{'='*80}")
    print(f"TRANSCRIPT FORMAT ANALYSIS - {len(results)} FILES")
    print(f"{'='*80}\n")

    # Counts
    single_line_count = sum(1 for r in results if r['single_line'])
    has_paragraphs_count = sum(1 for r in results if r['has_paragraphs'])
    has_song_count = sum(1 for r in results if r['has_song_lyrics'])
    has_radio_intro_count = sum(1 for r in results if r['has_radio_intro'])
    has_pastor_intro_count = sum(1 for r in results if r['has_pastor_intro'])
    has_closing_contact_count = sum(1 for r in results if r['has_closing_contact'])
    has_closing_promo_count = sum(1 for r in results if r['has_closing_promo'])
    ends_with_amen_count = sum(1 for r in results if r['ends_with_amen'])

    print(f"FORMAT ISSUES:")
    print(f"  Single-line files (< 10 lines): {single_line_count}/{len(results)} ({single_line_count/len(results)*100:.1f}%)")
    print(f"  Has proper paragraphs: {has_paragraphs_count}/{len(results)} ({has_paragraphs_count/len(results)*100:.1f}%)")

    print(f"\nOPENING BOILERPLATE:")
    print(f"  Song lyrics: {has_song_count}/{len(results)} ({has_song_count/len(results)*100:.1f}%)")
    print(f"  Radio intro: {has_radio_intro_count}/{len(results)} ({has_radio_intro_count/len(results)*100:.1f}%)")
    print(f"  Pastor intro: {has_pastor_intro_count}/{len(results)} ({has_pastor_intro_count/len(results)*100:.1f}%)")

    print(f"\nCLOSING BOILERPLATE:")
    print(f"  Contact info: {has_closing_contact_count}/{len(results)} ({has_closing_contact_count/len(results)*100:.1f}%)")
    print(f"  Promotional content: {has_closing_promo_count}/{len(results)} ({has_closing_promo_count/len(results)*100:.1f}%)")
    print(f"  Ends with 'Amen.': {ends_with_amen_count}/{len(results)} ({ends_with_amen_count/len(results)*100:.1f}%)")

    print(f"\nWORD COUNT STATISTICS:")
    word_counts = [r['word_count'] for r in results]
    print(f"  Min: {min(word_counts):,} words")
    print(f"  Max: {max(word_counts):,} words")
    print(f"  Avg: {sum(word_counts)//len(word_counts):,} words")
    print(f"  Median: {sorted(word_counts)[len(word_counts)//2]:,} words")

    # Detailed per-file analysis
    print(f"\n{'='*80}")
    print(f"DETAILED FILE ANALYSIS")
    print(f"{'='*80}\n")

    for i, r in enumerate(results, 1):
        print(f"{i}. {r['filename'][:60]}")
        print(f"   Lines: {r['total_lines']} | Words: {r['word_count']:,} | Single-line: {r['single_line']}")
        print(f"   Opening: Song={r['has_song_lyrics']} | Radio={r['has_radio_intro']} | Pastor={r['has_pastor_intro']}")
        print(f"   Closing: Contact={r['has_closing_contact']} | Promo={r['has_closing_promo']} | Amen={r['ends_with_amen']}")
        print(f"   Start: {r['start'][:80]}...")
        print(f"   End: ...{r['end'][-80:]}")
        print()

if __name__ == '__main__':
    main()
