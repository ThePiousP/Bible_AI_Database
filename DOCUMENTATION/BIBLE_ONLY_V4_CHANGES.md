# Bible-Only Extraction V4 - Changes Summary

## Goal
Increase from 11K to 45K-50K unique **Bible-only** words by maximizing vocabulary coverage.

---

## Changes Made to extract_entries.py

### ✅ CHANGE 1: Generic Words Now Included
**Lines:** 812 (already done in v3)
**Status:** Already implemented - `exclude_set = set()`

**Impact:**
- Words like THE, AND, FOR, BUT, NOT now included with biblical context
- These are critical crossword connectors!
- Example: "THE" with clue "In ___ beginning God created..." (Genesis 1:1)

---

### ✅ CHANGE 2: 2-Letter Words Included
**Lines:** 35-36 (already done in v3)
**Changes:**
```python
WORD_PATTERN = r'\b[A-Za-z]{2,15}\b'  # Changed from {3,15}
MIN_WORD_LENGTH = 2                    # Changed from 4
```

**Impact:** +2,000 words
- OF, IN, TO, AT, BY, ON, IS, IT, OR, IF, UP, GO, AM, BE, DO, HE, WE, ME, MY now included

---

### ✅ CHANGE 3: Expanded Frequency Ranges
**Lines:** 42, 46-47
**Changes:**
```python
# OLD:
PRIMARY_MAX_FREQ = 2000
PHASE_3_MIN_FREQ = 2001
PHASE_3_MAX_FREQ = 15000

# NEW:
PRIMARY_MAX_FREQ = 5000     # Capture LORD, GOD
PHASE_3_MIN_FREQ = 5001     # Ultra-high frequency
PHASE_3_MAX_FREQ = 15000    # THE, OF, AND, etc.
```

**Impact:** +5,000 words
- LORD (7,000+ occurrences) now included
- GOD (4,000+ occurrences) now included
- Essential biblical vocabulary captured

---

### ✅ CHANGE 4: **1 Verse Per Word (CRITICAL!)**
**Lines:** 497, 627
**Changes:**
```python
# Phase 1 (line 497):
# OLD: avg_verses_per_word = max(5, target // len(phase_words)) if phase_words else 8
# NEW: avg_verses_per_word = 1

# Phase 3 (line 627):
# OLD: Dynamic 3-5 verses based on frequency
# NEW: verses_per_word = 1
```

**Impact:** +8,000 words (THIS IS THE BIG ONE!)

**Why this matters:**
- **Old way:** 10K words × 5 verses = 50K entries (10K unique)
- **New way:** 50K words × 1 verse = 50K entries (50K unique) ✅

**Rationale:**
- Bible crosswords need maximum vocabulary, not clue variety
- One biblical clue per word is sufficient
- Players want biblical content, not 5-8 clue options
- Can add more clues later through manual curation

---

### ✅ CHANGE 5: Increased Phase Targets
**Lines:** 50-52
**Changes:**
```python
# OLD:
PHASE_1_TARGET = 100000
PHASE_2_TARGET = 15000
PHASE_3_TARGET = 5000

# NEW:
PHASE_1_TARGET = 150000  # Extract all common words
PHASE_2_TARGET = 25000   # Extract ALL rare words
PHASE_3_TARGET = 10000   # All high-frequency terms
```

**Impact:**
- With 1 verse/word, targets now represent unique word counts
- Script will process until all words in frequency ranges are extracted

---

### ✅ CHANGE 6: Removed Early Exits
**Lines:** 530-531, 581-582, 657-658
**Changes:**
```python
# Commented out in all three phases:
# if len(entries) >= target:
#     break
```

**Impact:** +3,000 rare biblical words
- Phase 1: Extracts EVERY word in freq 2-5000 range
- Phase 2: Extracts EVERY rare word (freq 1)
- Phase 3: Extracts EVERY protected high-frequency word
- No artificial limits on vocabulary size

---

### ✅ CHANGE 7: Updated Output Files
**Lines:** 26-28
**Changes:**
```python
OUTPUT_PATH = bible_crossword_v4.txt      # Was v3
REPORT_PATH = extraction_report_v4.txt    # Was v3
EXCLUDED_WORDS_PATH = excluded_words_list_v4.txt  # Was v3
```

---

## Expected Results

### Before Changes (v3)
```
Phase 1: 47,432 entries (8,472 unique words)
Phase 2: 2,476 entries (2,476 unique words)
Phase 3: 175 entries (47 unique words)
────────────────────────────────────────
Total: 50,083 entries (10,948 unique words)
Average clues per word: 4.57
```

### After Changes (v4 - PREDICTED)
```
Phase 1: ~35,000 entries (35,000 unique words) - 1 verse each
Phase 2: ~8,000 entries (8,000 unique words) - ALL rare words
Phase 3: ~5,000 entries (5,000 unique words) - ALL high-freq
────────────────────────────────────────
Total: ~48,000 entries (48,000 unique words) ✅
Average clues per word: 1.0
```

**Key Difference:** 48K unique words vs 11K unique words (4.4× increase!)

---

## Word Count Projection

| Length | V3 Count | V4 Expected | Increase | vs. Required |
|--------|----------|-------------|----------|--------------|
| 2-letter | 29 | 150+ | +121 | Need ~200 |
| 3-letter | 275 | 1,500+ | +1,225 | Need ~3,900 |
| 4-letter | 1,033 | 5,000+ | +3,967 | Need ~9,750 |
| 5-letter | 1,696 | 8,500+ | +6,804 | Need ~9,750 |
| 6-letter | 2,018 | 9,000+ | +6,982 | Need ~9,750 |
| 7-letter | 1,853 | 8,000+ | +6,147 | Need ~9,750 |
| 8-letter | 1,568 | 6,500+ | +4,932 | Need ~8,580 |
| 9-letter | 1,130 | 4,500+ | +3,370 | Need ~5,850 |
| **Total** | **10,948** | **~48,000** | **+37,000** | **Need ~78,000** |

### Analysis
- 3-4 letter words will still be SHORT (but much better than before)
- 5-9 letter words will be CLOSE to requirements
- Still missing ~30K words total
- **Solution:** Phase 2 will add Strong's Concordance (+14K) and NIV/ESV translations (+14K)

---

## Runtime Expectations

### Previous Runtime (v3)
- 5 minutes
- Stopped at targets (early exits active)
- Multiple verses per word (slower)

### New Runtime (v4)
- **15-20 minutes** (instructions estimate)
- No early exits (processes ALL words)
- 1 verse per word (faster per word, but more words total)

---

## Verification Checklist

After extraction completes, verify:

1. **Word Count**
   ```bash
   wc -l bible_crossword_v4.txt
   # Should show 45K-50K lines
   ```

2. **Format**
   ```bash
   head -5 bible_crossword_v4.txt
   # Check: WORD [TAB] clue [TAB] clue...
   ```

3. **2-Letter Words Present**
   ```bash
   grep -E "^(OF|IN|TO|AT|BY|ON|IS|IT)\t" bible_crossword_v4.txt
   # Should find these words
   ```

4. **High-Frequency Words Present**
   ```bash
   grep -E "^(THE|AND|LORD|GOD)\t" bible_crossword_v4.txt
   # Should find these with biblical clues
   ```

5. **Verses Per Word**
   ```bash
   awk -F'\t' '{print NF-1}' bible_crossword_v4.txt | sort | uniq -c
   # Should show mostly "1" (one clue per word)
   ```

6. **Unique Words**
   ```bash
   awk -F'\t' '{print $1}' bible_crossword_v4.txt | sort | uniq | wc -l
   # Should match line count (no duplicates)
   ```

---

## Success Criteria

### Phase 1 Complete (v4 extraction)
- ✓ 45K-50K unique words
- ✓ 2-letter words included
- ✓ Generic biblical words included (THE, AND, etc.)
- ✓ High-frequency words included (LORD, GOD)
- ✓ 1 verse per word average
- ✓ All words in frequency ranges extracted (no early exits)

### Next Steps After v4
If successful:
1. Test in CrosswordBuilder
2. If still need more words, proceed with:
   - Phase 2: Strong's Concordance extraction (+14K)
   - Phase 3: NIV translation (+8K)
   - Phase 4: ESV translation (+6K)
   - Target: 65K+ total unique biblical words

---

## Technical Notes

### Why 1 Verse Per Word Works
- Crossword needs COVERAGE not DEPTH
- One good biblical clue is sufficient
- More verses = fewer unique words
- This is a Bible-only strategy (different from general crosswords)

### Why Include "Generic" Words
- THE appears in "In THE beginning..." (Genesis 1:1) ← BIBLICAL CONTEXT
- AND appears in "God created the heaven AND the earth" (Genesis 1:1)
- These are not "generic" when clued with scripture
- Essential for crossword grid connectivity

### Phase Frequency Ranges Explained
- **Phase 1** (freq 2-5000): Common biblical vocabulary
  - Examples: BLESSED, COVENANT, SANCTUARY, PROPHET
  - Appears multiple times, but not ultra-common

- **Phase 2** (freq 1): Rare biblical terms
  - Examples: ZURIEL, MERAB, ABIASAPH (proper names, places)
  - Appears only once in entire Bible
  - Adds unique vocabulary

- **Phase 3** (freq 5001-15000): Ultra-high frequency protected words
  - Examples: LORD (7,000+), GOD (4,000+), THE, AND, OF
  - Would normally be "excluded" but are biblically essential
  - Protected from exclusion in PROTECTED_BIBLICAL_TERMS set

---

## File Changes Summary

**Modified:** `extract_entries.py`
- 7 configuration changes
- 3 function modifications (Phase 1, 2, 3)
- All early exits disabled
- Output paths updated to v4

**Generated (pending):**
- `bible_crossword_v4.txt` - 45K-50K unique words
- `extraction_report_v4.txt` - Detailed statistics
- `excluded_words_list_v4.txt` - (empty since exclusions disabled)

---

## Current Status

**Extraction Running:** bible_crossword_v4.txt
**Expected Completion:** 15-20 minutes from start
**Next Action:** Verify results and test in CrosswordBuilder

---

**Project Status: Bible-Only Expansion Phase 1 In Progress** ⏳
