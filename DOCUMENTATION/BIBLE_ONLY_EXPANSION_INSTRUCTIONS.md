# BIBLE-ONLY CROSSWORD EXPANSION STRATEGY
**Project:** Bible Crossword Game - Vocabulary Expansion
**Goal:** Increase from 11K to 50K+ unique biblical words
**Strategy:** Maximize unique words, minimize verses per word

---

## CURRENT SITUATION

### Problem
- Current extraction: 10,947 unique words
- CrosswordBuilder needs: ~78,000 words for optimal generation
- Bible-only crosswords require: Minimum 40K-50K biblical words
- Gap: 67,000 words (86% short!)

### Root Cause
Current script optimizes for:
- ❌ Multiple verses per word (5-8 verses each)
- ❌ Excluding "generic" words that appear in Bible
- ❌ Limited frequency ranges
- ❌ 3+ letter words only

Bible-only crosswords need:
- ✅ Maximum unique words (1 verse per word is enough!)
- ✅ ALL words that appear in Bible (including THE, AND, etc.)
- ✅ Full frequency spectrum
- ✅ 2+ letter words

---

## EXPANSION ROADMAP

| Phase | Strategy | Expected Gain | New Total |
|-------|----------|---------------|-----------|
| Current | Base KJV extraction | - | 11,000 |
| Phase 1 | Include "generic" words | +8,000 | 19,000 |
| Phase 2 | Add 2-letter words | +2,000 | 21,000 |
| Phase 3 | Expand frequency ranges | +5,000 | 26,000 |
| Phase 4 | Change to 1 verse/word | +8,000 | 34,000 |
| Phase 5 | Maximize rare words | +3,000 | 37,000 |
| Phase 6 | Strong's Concordance | +14,000 | 51,000 |
| Phase 7 | NIV translation | +8,000 | 59,000 |
| Phase 8 | ESV translation | +6,000 | 65,000 |

**Target: 50K-65K unique biblical words**

---

## PRIORITY 1: MODIFY EXTRACTION SCRIPT (IMMEDIATE)

### File: `extract_crossword_entries.py`

All modifications below are for the existing KJV extraction script.

---

### CHANGE 1: Remove Generic Word Exclusions

**Current Problem:**
- Lines 91-108 define GENERIC_ENGLISH set
- Excludes THE, AND, BUT, FOR, etc.
- These words ARE in the Bible and need biblical context!

**Action:**
```python
# Lines 91-108: Comment out or delete entire GENERIC_ENGLISH set
# These words appear in Bible verses and should have biblical clues!

# OLD (DELETE THIS):
# GENERIC_ENGLISH = {
#     'THE', 'AND', 'BUT', 'FOR', 'NOT', 'YOU', ...
# }

# NEW: Just remove it entirely - it's not used anymore since exclude_set = set()
```

**Verification:**
- Line 809 should have: `exclude_set = set()`
- This ensures no words are excluded

**Expected Result:** +8,000 words

---

### CHANGE 2: Include 2-Letter Words

**Current Problem:**
- Line 35: `WORD_PATTERN = r'\b[A-Za-z]{3,15}\b'` - only 3-15 letters
- Line 36: `MIN_WORD_LENGTH = 4` - rejects short words
- Misses: OF, IN, TO, AT, BY, ON, IS, IT, OR, IF, UP, GO, AM, BE, DO, HE, WE, ME, MY

**Action:**
```python
# Line 35: Change word pattern to capture 2-letter words
WORD_PATTERN = r'\b[A-Za-z]{2,15}\b'  # Changed from {3,15}

# Line 36: Lower minimum word length
MIN_WORD_LENGTH = 2  # Changed from 4

# Line 38: Keep this as is
INCLUDE_3_LETTER = True  # Still needed for validation logic
```

**Expected Result:** +2,000 words

---

### CHANGE 3: Expand Frequency Ranges

**Current Problem:**
- Line 42: `PRIMARY_MAX_FREQ = 500` - excludes common words like LORD (5000+x)
- Phase 3 only captures 25-1000 range
- Misses very high-frequency biblical terms

**Action:**
```python
# Line 42: Increase primary range maximum
PRIMARY_MAX_FREQ = 5000  # Changed from 500

# After line 43, add new Phase 3 configuration:
PHASE_3_MIN_FREQ = 5001   # Words appearing 5001+ times
PHASE_3_MAX_FREQ = 15000  # Up to 15,000 occurrences
```

**Rationale:**
- LORD appears ~7,000 times
- GOD appears ~4,000 times
- These are ESSENTIAL biblical words!

**Expected Result:** +5,000 words

---

### CHANGE 4: Change to 1 Verse Per Word (CRITICAL!)

**Current Problem:**
- Line 492: Calculates 5-8 verses per word
- This creates QUALITY (multiple clues) not QUANTITY (unique words)
- For Bible-only, we need EVERY possible unique word!

**Action:**
```python
# Line 492: Force exactly 1 verse per word
# OLD:
# avg_verses_per_word = max(5, target // len(phase_words)) if phase_words else 8

# NEW:
avg_verses_per_word = 1  # Changed: maximize unique words, not clues per word

# Explanation comment:
# For Bible-only crosswords, we need maximum unique words.
# One biblical clue per word is sufficient; we can add more clues later if needed.
```

**This is the MOST IMPORTANT change!**
- Old way: 10K words × 5 verses = 50K entries (10K unique)
- New way: 50K words × 1 verse = 50K entries (50K unique) ✅

**Expected Result:** +8,000 words (from capturing more unique words in same extraction time)

---

### CHANGE 5: Increase Phase Targets

**Current Problem:**
- Line 47: `PHASE_1_TARGET = 100000` - this is entries, not words
- With 1 verse per word, target needs to match word count goal

**Action:**
```python
# Line 47: Increase Phase 1 target (represents unique words now)
PHASE_1_TARGET = 150000  # Changed from 100000

# Line 48: Maximize rare words
PHASE_2_TARGET = 25000   # Changed from 10000 - extract ALL rare words

# Line 49: Increase protected words
PHASE_3_TARGET = 10000   # Changed from 2000
```

**Expected Result:** Script will extract until all words in range are captured

---

### CHANGE 6: Remove Early Exit in Phase 2

**Current Problem:**
- Lines 524-525 in extract_phase_1() stop when target reached
- We want EVERY rare word, not just first 10K

**Action:**
```python
# In extract_phase_2() function (around line 560):
# Find these lines:
#     if len(entries) >= target:
#         break

# COMMENT THEM OUT:
# For Bible-only, extract EVERY rare word without limit
#     # if len(entries) >= target:
#     #     break
```

**Expected Result:** +3,000 rare biblical words (proper names, places, theological terms)

---

### CHANGE 7: Update Configuration Comments

**Action:**
```python
# Line 46-49 comments: Update to reflect new strategy
# Phase targets (1 verse per word - maximize unique vocabulary)
PHASE_1_TARGET = 150000  # Common words (2-5000x frequency)
PHASE_2_TARGET = 25000   # Rare words (1x frequency) - extract ALL
PHASE_3_TARGET = 10000   # High-frequency biblical terms (5001-15000x)
```

---

## SUMMARY OF SCRIPT CHANGES

### Configuration Section (Lines 35-49)
```python
# Word pattern and length
WORD_PATTERN = r'\b[A-Za-z]{2,15}\b'  # CHANGED: 2-15 letters (was 3-15)
MIN_WORD_LENGTH = 2                    # CHANGED: Allow 2-letter words (was 4)
MAX_WORD_LENGTH = 15
INCLUDE_3_LETTER = True

# Frequency ranges
PRIMARY_MIN_FREQ = 2
PRIMARY_MAX_FREQ = 5000                # CHANGED: Capture high-freq words (was 500)
SECONDARY_FREQ = 1
PHASE_3_MIN_FREQ = 5001                # NEW: Ultra-high frequency
PHASE_3_MAX_FREQ = 15000               # NEW: Capture THE, LORD, GOD, etc.

# Phase targets (1 verse per word - maximize unique vocabulary)
PHASE_1_TARGET = 150000  # CHANGED: Increased (was 100000)
PHASE_2_TARGET = 25000   # CHANGED: Extract ALL rare words (was 10000)
PHASE_3_TARGET = 10000   # CHANGED: Increased (was 2000)
```

### Exclusions Section (Lines 91-108)
```python
# DELETE or COMMENT OUT entire GENERIC_ENGLISH set
# These words appear in the Bible and should have biblical clues!
```

### Verses Per Word (Line 492)
```python
# extract_phase_1() function
avg_verses_per_word = 1  # CHANGED: Maximize unique words (was 5-8)
```

### Phase 2 Early Exit (Lines 560+)
```python
# extract_phase_2() function
# COMMENT OUT the early exit:
#     if len(entries) >= target:
#         break
```

---

## EXPECTED RESULTS AFTER CHANGES

### Before Changes
```
Phase 1: 29,312 entries (8,333 unique words)
Phase 2: 2,473 entries (2,473 unique words)
Phase 3: 957 entries (328 unique words)
Total: 32,742 entries (10,947 unique words)
```

### After Changes
```
Phase 1: 35,000 entries (35,000 unique words) - 1 verse each
Phase 2: 8,000 entries (8,000 unique words) - ALL rare words
Phase 3: 5,000 entries (5,000 unique words) - High-frequency terms
Total: 48,000 entries (48,000 unique words) ✅
```

**Key Difference:** 48K unique words vs 11K unique words (4.4× increase!)

---

## RUN THE MODIFIED SCRIPT

### Command
```bash
cd D:\Project_PP\projects\bible
python extract_crossword_entries.py
```

### Expected Runtime
- 15-20 minutes (processing more words)
- Watch for progress messages every 500 words

### Output Files
```
bible_crossword_v4.txt       - New extraction with 48K unique words
extraction_report_v4.txt     - Statistics report
```

### Verification Checks
1. **Unique word count:** Should be 45K-50K (vs 11K before)
2. **2-letter words present:** OF, IN, TO, AT, BY, etc.
3. **High-frequency words present:** THE, AND, LORD, GOD
4. **Format correct:** WORD [TAB] clue [TAB] clue [TAB] ...
5. **Verses per word:** Average should be ~1.0 (vs 4.6 before)

---

## PRIORITY 2: STRONG'S CONCORDANCE INTEGRATION

### File: `extract_strongs_entries.py` (NEW SCRIPT)

Create new script to extract Strong's concordance as biblical vocabulary.

### Database Info
- Location: `D:\Project_PP\projects\bible\data\concordance.db`
- Contains: 14,298 Hebrew/Greek word entries
- Structure: Strong's number, transliteration, definition, part of speech

### Script Purpose
Extract Strong's entries as crossword words with biblical definitions.

### Example Output
```
PROPITIATION    Greek hilasterion: atoning sacrifice    Romans 3:25
CHESED          Hebrew: lovingkindness, mercy           Psalm 136:1
LOGOS           Greek: word, reason, divine utterance   John 1:1
RUACH           Hebrew: spirit, wind, breath            Genesis 1:2
```

### Script Structure
```python
#!/usr/bin/env python3
"""
Strong's Concordance Crossword Entry Extractor
Extracts Hebrew/Greek words as biblical vocabulary
"""

import sqlite3

DB_PATH = r"D:\Project_PP\projects\bible\data\concordance.db"
OUTPUT_PATH = r"D:\Project_PP\projects\bible\strongs_crossword.txt"

def extract_strongs_entries():
    """
    Extract Strong's entries as crossword words
    Format: WORD [TAB] definition [TAB] example verse reference
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Query structure depends on concordance.db schema
    # Typical schema:
    # - strongs_number (e.g., H2617, G3056)
    # - transliteration (e.g., "chesed", "logos")
    # - definition (e.g., "lovingkindness, mercy")
    # - part_of_speech (e.g., "noun")
    
    query = """
        SELECT transliteration, definition, example_verse
        FROM concordance
        WHERE transliteration IS NOT NULL
        AND length(transliteration) >= 3
        AND length(transliteration) <= 15
        ORDER BY transliteration
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    entries = []
    for word, definition, example in results:
        # Clean and format
        word_clean = word.upper().strip()
        
        # Create clue from definition
        clue = f"Strong's: {definition}"
        
        # Add example verse if available
        if example:
            clue += f" ({example})"
        
        entries.append(f"{word_clean}\t{clue}")
    
    # Write output
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(entry + '\n')
    
    print(f"Extracted {len(entries):,} Strong's entries")
    conn.close()

if __name__ == "__main__":
    extract_strongs_entries()
```

### Action Required
1. Examine `concordance.db` schema (use DB Browser for SQLite)
2. Identify correct table and column names
3. Adjust query accordingly
4. Run script to generate `strongs_crossword.txt`

### Expected Result
+14,000 biblical words with theological definitions

---

## PRIORITY 3: MULTIPLE TRANSLATION EXTRACTION

### Strategy
Extract from NIV and ESV translations to add vocabulary variants.

### Process

#### Step 1: Scrape NIV Translation
```python
# Modify Bible scraper script
version = "NIV"  # Change from "KJV"
# Run scraper to create NIV database
```

#### Step 2: Run Extraction on NIV
```python
# Point extract_crossword_entries.py at NIV database
DB_PATH = r"D:\Project_PP\projects\bible\data\NIV_GoodBook.db"
OUTPUT_PATH = r"D:\Project_PP\projects\bible\bible_crossword_NIV.txt"
# Run extraction
```

#### Step 3: Merge Unique Words Only
```python
#!/usr/bin/env python3
"""
Merge translations - keep only NEW unique words
"""

def merge_translations():
    # Load KJV words
    kjv_words = set()
    with open('bible_crossword_v4.txt', 'r') as f:
        for line in f:
            word = line.split('\t')[0].strip()
            kjv_words.add(word)
    
    # Load NIV, keep only new words
    niv_unique = []
    with open('bible_crossword_NIV.txt', 'r') as f:
        for line in f:
            word = line.split('\t')[0].strip()
            if word not in kjv_words:
                niv_unique.append(line)
    
    # Write merged file
    with open('bible_crossword_merged.txt', 'w') as f:
        # Copy all KJV entries
        with open('bible_crossword_v4.txt', 'r') as kjv:
            f.write(kjv.read())
        # Add unique NIV entries
        for line in niv_unique:
            f.write(line)
    
    print(f"Added {len(niv_unique):,} new words from NIV")

if __name__ == "__main__":
    merge_translations()
```

#### Step 4: Repeat for ESV
Same process with ESV translation.

### Expected Results
- NIV: +8,000 unique words
- ESV: +6,000 unique words
- Total: +14,000 words

---

## PRIORITY 4: FINAL CONSOLIDATION

### After All Extractions Complete

Combine all sources into master file:

```python
#!/usr/bin/env python3
"""
Consolidate all Bible sources into master crossword file
"""

def consolidate_all_sources():
    sources = [
        'bible_crossword_v4.txt',      # KJV expanded (48K words)
        'strongs_crossword.txt',       # Strong's (14K words)
        'bible_crossword_NIV.txt',     # NIV unique (8K words)
        'bible_crossword_ESV.txt'      # ESV unique (6K words)
    ]
    
    all_words = {}
    
    for source in sources:
        with open(source, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 2:
                    continue
                
                word = parts[0]
                clues = parts[1:]
                
                if word not in all_words:
                    all_words[word] = []
                
                all_words[word].extend(clues)
    
    # Write consolidated file
    with open('bible_crossword_master.txt', 'w', encoding='utf-8') as f:
        for word in sorted(all_words.keys()):
            clues = all_words[word]
            line = word + '\t' + '\t'.join(clues) + '\n'
            f.write(line)
    
    print(f"Master file created: {len(all_words):,} unique words")
    
    # Generate statistics
    lengths = {}
    for word in all_words:
        length = len(word)
        lengths[length] = lengths.get(length, 0) + 1
    
    print("\nWord Length Distribution:")
    for length in sorted(lengths.keys()):
        print(f"{length:2d} letters: {lengths[length]:6,} words")

if __name__ == "__main__":
    consolidate_all_sources()
```

### Expected Final Result
```
Master File: 65,000+ unique biblical words
- KJV expanded: 48,000
- Strong's: 14,000
- NIV unique: 8,000
- ESV unique: 6,000
- Duplicates removed: -11,000
Total: ~65,000 unique words
```

---

## TESTING & VALIDATION

### After Each Extraction Phase

1. **Word Count Check**
   ```bash
   wc -l bible_crossword_v4.txt
   # Should show 45K-50K lines
   ```

2. **Sample Verification**
   ```bash
   head -5 bible_crossword_v4.txt
   # Check format: WORD [TAB] clue [TAB] clue...
   ```

3. **Length Distribution**
   ```bash
   awk -F'\t' '{print length($1)}' bible_crossword_v4.txt | sort | uniq -c
   # Should show words from 2-15 letters
   ```

4. **Duplicate Check**
   ```bash
   awk -F'\t' '{print $1}' bible_crossword_v4.txt | sort | uniq -d
   # Should show NO duplicates (empty output)
   ```

5. **Generic Words Present**
   ```bash
   grep -E "^(THE|AND|FOR|BUT|NOT)\t" bible_crossword_v4.txt
   # Should find these words with biblical clues
   ```

### CrosswordBuilder Integration Test

1. Copy `bible_crossword_v4.txt` to Unity project:
   ```
   D:\Project_PP\Unity\Bible Crossword\Assets\Crossword\CrosswordBuilder\Data\
   ```

2. Configure CrosswordBuilder to use new file

3. Generate test puzzle:
   - Should complete without errors
   - Should use biblical words only
   - Grid should fill properly

4. Verify puzzle quality:
   - Check clues are biblical verses
   - Verify no generic/secular clues present
   - Test multiple puzzle generations

---

## TROUBLESHOOTING

### Issue: Still not enough words
**Solution:** 
- Extract more translations (NKJV, NASB, AMP)
- Include biblical names database
- Add theological terms from systematic theology texts

### Issue: Script runs out of memory
**Solution:**
- Process in batches (by book)
- Write to file incrementally
- Use database cursors with fetchmany()

### Issue: Duplicate words appearing
**Solution:**
- Add deduplication step after each extraction
- Use set() to track already-extracted words
- Run consolidation script to merge duplicates

### Issue: Poor quality clues
**Solution:**
- Increase MIN_VERSE_LENGTH (line 52)
- Improve verse scoring algorithm
- Filter out verses with too many blanks

---

## SUCCESS METRICS

### Phase 1 Complete (Modified KJV Extraction)
- ✅ 45K-50K unique words
- ✅ 2-letter words included
- ✅ Generic biblical words included
- ✅ High-frequency words included
- ✅ 1 verse per word average

### Phase 2 Complete (Strong's Added)
- ✅ 60K+ unique words
- ✅ Theological terms included
- ✅ Hebrew/Greek transliterations

### Phase 3 Complete (Multi-Translation)
- ✅ 65K+ unique words
- ✅ Translation variants included
- ✅ Modern English vocabulary

### Final Goal
- ✅ 65,000+ unique biblical words
- ✅ Bible-only crossword generation possible
- ✅ Professional quality puzzles
- ✅ Pure biblical content (no secular words)

---

## TIMELINE ESTIMATE

| Task | Time | Cumulative |
|------|------|------------|
| Modify extraction script | 30 min | 30 min |
| Run modified extraction (KJV) | 20 min | 50 min |
| Verify results | 15 min | 1h 5min |
| Create Strong's extractor | 45 min | 1h 50min |
| Run Strong's extraction | 5 min | 1h 55min |
| Scrape NIV translation | 30 min | 2h 25min |
| Extract NIV | 20 min | 2h 45min |
| Scrape ESV translation | 30 min | 3h 15min |
| Extract ESV | 20 min | 3h 35min |
| Merge all sources | 30 min | 4h 5min |
| Test in CrosswordBuilder | 30 min | 4h 35min |

**Total: ~5 hours of work** (spread over 2-3 days with test time)

---

## PRIORITY ORDER

### DO FIRST (Today)
1. ✅ Modify extract_crossword_entries.py (all changes above)
2. ✅ Run modified extraction
3. ✅ Verify 45K-50K words achieved

### DO SECOND (Tomorrow)
4. Create Strong's extractor script
5. Run Strong's extraction
6. Merge with KJV extraction

### DO THIRD (Day 3)
7. Test consolidated file in CrosswordBuilder
8. If sufficient, deploy game
9. If not, proceed with multi-translation extraction

---

## NOTES

### Why 1 Verse Per Word?
- Bible crosswords don't need 5-8 clue options per puzzle
- Players want biblical content, not clue variety
- Maximizing unique words is more important than clue variety
- Can always add more clues later through manual curation

### Why Include "Generic" Words?
- THE appears in "In THE beginning..." (Genesis 1:1)
- AND appears in "God created the heaven AND the earth" (Genesis 1:1)
- These words have BIBLICAL context when clued with scripture
- Essential for crossword grid connectivity

### Why Strong's Concordance?
- Adds theological vocabulary (PROPITIATION, REDEMPTION, SANCTIFICATION)
- Hebrew/Greek transliterations are unique words (CHESED, LOGOS, RUACH)
- Provides scholarly biblical terminology
- Enriches the "biblical" nature of crosswords

### Why Multiple Translations?
- Different English vocabulary (LOVINGKINDNESS vs UNFAILING LOVE)
- Modern translations more accessible to younger players
- Expands total unique word count significantly
- Provides translation variety for advanced players

---

## END OF INSTRUCTIONS

**Next Action:** Modify `extract_crossword_entries.py` with all changes listed above, then run extraction.

**Expected Result:** 45K-50K unique biblical words ready for Bible-only crossword generation.

**Questions:** Contact Aaron if script modifications unclear or extraction results differ significantly from projections.
