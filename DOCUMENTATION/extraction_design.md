# Crossword Entry Extraction Design Document

## Executive Summary

Based on comprehensive analysis of GoodBook.db, we have determined that **extracting 50,000 quality crossword entries is highly feasible**. The database contains 12,988 unique words (3-15 letters), with 8,896 words in the optimal frequency range (2-500 occurrences) that appear an average of 25.6 times each. This gives us sufficient material to generate quality entries.

---

## 1. EXTRACTION STRATEGY OVERVIEW

### Three-Phase Approach

**Phase 1: Core Biblical Vocabulary** (Target: ~40,000 entries)
- Words appearing 2-500 times
- Highest quality biblical terms
- Multiple verses per word available

**Phase 2: Rare Biblical Terms** (Target: ~7,000 entries)
- Words appearing exactly 1 time
- Unique proper nouns and rare terms
- One verse per word (by definition)

**Phase 3: Common Biblical Context** (Target: ~3,000 entries)
- Words appearing 501-1000 times
- Cherry-picked biblical terms only
- Avoid generic English

**Total: 50,000 entries**

---

## 2. WORD FILTERING RULES

### A. Frequency Filtering

```python
PRIMARY_MIN_FREQUENCY = 2
PRIMARY_MAX_FREQUENCY = 500
SECONDARY_FREQUENCY = 1  # Rare words
TERTIARY_MIN_FREQUENCY = 501
TERTIARY_MAX_FREQUENCY = 1000
```

### B. Length Filtering

```python
MIN_WORD_LENGTH = 4
MAX_WORD_LENGTH = 12
INCLUDE_3_LETTER = True  # For biblical terms like "ARK", "GOD"
```

**Rationale:** Analysis showed 96.6% of words are 4-12 letters. Including select 3-letter words captures important biblical terms.

### C. Generic Word Exclusion

Based on analysis, exclude the top 200 most frequent words:

```python
GENERIC_WORDS_TO_EXCLUDE = [
    "THE", "AND", "YOU", "FOR", "HIS", "THAT", "SHALL", "YOUR",
    "THEY", "NOT", "WILL", "HIM", "WITH", "WHO", "ALL", "THEM",
    "FROM", "HAVE", "WAS", "BUT", "SAID", "THEN", "THEIR", "ARE",
    "WHICH", "WHEN", "WERE", "THIS", "ONE", "HAS", "HAD", "OUT",
    "THERE", "NOW", "ALSO", "CAME", "COME", "BEFORE", "AGAINST",
    "DAY", "LET", "THOSE", "MAY", "BECAUSE", "INTO", "SAYING",
    "WENT", "ITS", "WHAT", "MADE", "DID", "THESE", "LIKE", "OUR",
    "DOWN", "THINGS", "SAYS", "SAY", "OVER", "NOR", "MAKE", "AMONG",
    "SHE", "KNOW", "TAKE", "ACCORDING", "PUT", "AWAY", "TWO", "GIVE",
    "EVERY", "THUS", "WHOM", "TOOK", "GOOD", "BRING", "SEE", "AFTER",
    "SENT", "WOULD", "OWn", "UPON", "CALLED", "SHOULD", "MANY",
    "BEEN", "WAY", "DONE", "DOES", "MORE", "EAT", "SPOKE", "WHERE",
    "HIMSELF", "HEAR", "THROUGH", "HOW", "THAN", "SPEAK", "GIVEN",
    "ANY", "EVEN", "OTHER", "YET", "FIRST", "ANOTHER", "UNTIL",
    "AGAIN", "TOGETHER", "WHY", "INDEED", "BACK", "SOME", "OFF",
    "FOUND", "SIDE", "SUCH", "GREAT", "PLACE", "WORD", "BEING",
    "BOTH", "EACH", "SAME", "EVER", "STILL", "WHILE", "SINCE",
    "MUCH", "WITHIN", "WITHOUT", "ABOUT", "HAVING", "DURING",
    "BEFORE", "AFTER", "ABOVE", "BELOW", "BETWEEN", "UNDER",
    "AGAIN", "FURTHER", "THEN", "ONCE", "HERE", "THERE", "VERY",
    "ONLY", "JUST", "ALSO", "WELL", "SURE", "NEVER", "ALWAYS",
    "OFTEN", "SOON", "HOWEVER", "ALTHOUGH", "THOUGH", "WHETHER",
    "NEITHER", "EITHER", "BOTH", "FEW", "SEVERAL", "ENOUGH",
    "MOST", "LEAST", "LESS", "FEWER", "MANY", "MUCH", "SOMETHING",
    "NOTHING", "ANYTHING", "EVERYTHING", "SOMEONE", "ANYONE",
    "EVERYONE", "NOBODY", "ANYBODY", "EVERYBODY"
    # ... (will load top 200 from analysis dynamically)
]
```

**Implementation:** Load from analysis results dynamically.

### D. Special Handling

**Proper Nouns:** INCLUDE - they make excellent crossword entries
- Examples: AARON, MOSES, JERUSALEM, BETHLEHEM

**Numbers:** EXCLUDE - not useful for crosswords
- Examples: THREE, SEVEN, HUNDRED, THOUSAND

**Contractions:** EXCLUDE - apostrophes don't work in crosswords
- Pattern: `\w+'\w+` (e.g., "DON'T", "WON'T")

---

## 3. VERSE SELECTION STRATEGY

### A. Multiple Verses Per Word

When a word appears in multiple verses, select verses using this priority:

```python
def select_verses_for_word(word, all_verses_with_word, target_verses_per_word):
    """
    Select best verses for a word

    Priority factors:
    1. Verse length (shorter is better for clues)
    2. Word appears only once in verse (avoid duplicates)
    3. Verse has good context (not just "and X said...")
    4. Distribute across different books (variety)
    """

    # Score each verse
    scored_verses = []
    for verse in all_verses_with_word:
        score = calculate_verse_score(verse, word)
        scored_verses.append((score, verse))

    # Sort by score and take top N
    scored_verses.sort(reverse=True)
    return scored_verses[:target_verses_per_word]
```

### B. Verse Scoring Algorithm

```python
def calculate_verse_score(verse_text, word):
    score = 100  # Base score

    # Factor 1: Length penalty (prefer 50-200 chars)
    verse_len = len(verse_text)
    if verse_len < 50:
        score -= 30  # Too short, lacks context
    elif verse_len > 300:
        score -= 20  # Too long, overwhelming clue
    elif 80 <= verse_len <= 200:
        score += 20  # Ideal length

    # Factor 2: Word count in verse (prefer single occurrence)
    word_count = verse_text.upper().count(word.upper())
    if word_count == 1:
        score += 30  # Perfect - single occurrence
    elif word_count == 2:
        score -= 10  # Manageable
    else:
        score -= 30  # Multiple occurrences problematic

    # Factor 3: Context quality
    # Avoid verses that are mostly lists
    if verse_text.count(',') > 5:
        score -= 15  # Likely a genealogy or list

    # Prefer verses with good sentence structure
    if '.' in verse_text or '?' in verse_text or '!' in verse_text:
        score += 10  # Complete sentence

    # Factor 4: Quote marks (direct speech often good context)
    if '"' in verse_text or '"' in verse_text:
        score += 5

    return score
```

### C. Verses Per Word Target

```python
def calculate_verses_needed(word_frequency, phase, target_total):
    """
    Dynamically calculate how many verses to extract per word
    """
    if phase == "PRIMARY":  # 2-500 frequency
        # Spread evenly
        return min(6, word_frequency)  # Max 6 verses per word

    elif phase == "SECONDARY":  # 1 frequency
        return 1  # By definition

    elif phase == "TERTIARY":  # 501-1000 frequency
        # Only take 1-2 verses from common words
        return min(2, word_frequency // 100)
```

---

## 4. WORD BLANKING LOGIC

### A. Basic Blanking Algorithm

```python
def blank_word_in_verse(verse_text, word):
    """
    Replace target word with "___" in verse

    Challenges:
    1. Case sensitivity (David vs DAVID vs david)
    2. Multiple occurrences in same verse
    3. Punctuation handling
    4. Possessives (David's)
    """

    # Strategy: Blank FIRST occurrence only
    # Use case-insensitive search, preserve original case context

    pattern = r'\b' + re.escape(word) + r'\b'

    # Find first match
    match = re.search(pattern, verse_text, re.IGNORECASE)
    if match:
        start, end = match.span()
        blanked = verse_text[:start] + "___" + verse_text[end:]
        return blanked

    return verse_text  # No match (shouldn't happen)
```

### B. Advanced Blanking (Handle Edge Cases)

```python
def smart_blank_word(verse_text, word):
    """
    Intelligent blanking with edge case handling
    """

    # Check if word appears multiple times
    pattern = r'\b' + re.escape(word) + r'\b'
    matches = list(re.finditer(pattern, verse_text, re.IGNORECASE))

    if len(matches) == 0:
        # Try partial match (possessives, plurals)
        pattern = r'\b' + re.escape(word)
        matches = list(re.finditer(pattern, verse_text, re.IGNORECASE))

    if len(matches) == 0:
        return None  # Can't blank - skip this verse

    # Blank the FIRST occurrence
    match = matches[0]
    start, end = match.span()

    # Extend to handle possessives ('s)
    if end < len(verse_text) and verse_text[end:end+2] == "'s":
        end += 2

    blanked = verse_text[:start] + "___" + verse_text[end:]

    # Verify blanking worked
    if "___" not in blanked:
        return None

    return blanked
```

### C. Duplicate Word Handling

For verses where word appears multiple times (77,437 cases found):

**Strategy 1: Blank first occurrence only** (PREFERRED)
- Cleanest for user
- Still provides good context
- Example: "David the king; and David..." → "___ the king; and David..."

**Strategy 2: Skip and use different verse**
- Avoid confusion
- Only use verses with single occurrence

**Strategy 3: Blank ALL occurrences**
- Creates multiple blanks
- May make clue harder
- Example: "___ the king; and ___ begat..."

**DECISION: Use Strategy 1** (blank first occurrence)

---

## 5. OUTPUT FORMAT

### A. Required Format for Unity Crossword

```
WORD<TAB>none<TAB>verse with ___ blank<TAB>Book Chapter:Verse
```

### B. Example Entries

```
AARON	none	Moreover the LORD said unto me, Take thee a great roll, and write in it with a man's pen concerning ___.	Isaiah 8:1
JERUSALEM	none	And I saw the holy city, ___, coming down from God out of heaven, prepared as a bride adorned for her husband.	Revelation 21:2
DAVID	none	And Jesse begat ___ the king; and David the king begat Solomon of her that had been the wife of Urias.	Matthew 1:6
```

### C. Reference Format

```python
def format_reference(book_name, chapter_num, verse_num):
    """
    Format: "Book Chapter:Verse"
    Examples: "Genesis 1:1", "Revelation 21:2"
    """
    return f"{book_name} {chapter_num}:{verse_num}"
```

### D. Text Cleaning

```python
def clean_verse_text(text):
    """
    Clean verse text for output
    """
    # Remove footnote markers
    text = re.sub(r'\[\d+\]', '', text)

    # Remove special unicode characters
    text = text.replace(''', "'")
    text = text.replace('"', '"')
    text = text.replace('"', '"')

    # Normalize whitespace
    text = ' '.join(text.split())

    # Remove leading/trailing punctuation from blanked verses
    text = text.strip()

    return text
```

---

## 6. QUALITY CONTROLS

### A. Entry Validation

Each entry must pass these checks before inclusion:

```python
def validate_entry(word, blanked_verse, reference):
    """
    Quality control checks
    """
    checks = []

    # Check 1: Word meets length requirements
    checks.append(MIN_WORD_LENGTH <= len(word) <= MAX_WORD_LENGTH)

    # Check 2: Blanked verse contains exactly one "___"
    checks.append(blanked_verse.count("___") == 1)

    # Check 3: Verse has minimum length (not just the word)
    checks.append(len(blanked_verse) >= 30)

    # Check 4: Verse has maximum length
    checks.append(len(blanked_verse) <= 500)

    # Check 5: Word is not in exclude list
    checks.append(word.upper() not in GENERIC_WORDS_TO_EXCLUDE)

    # Check 6: Reference is properly formatted
    checks.append(bool(re.match(r'.+ \d+:\d+', reference)))

    # Check 7: Original verse contained the word (sanity check)
    # (This should be checked before blanking)

    return all(checks)
```

### B. Duplicate Detection

```python
def detect_duplicates(entries):
    """
    Ensure no duplicate word+verse combinations
    """
    seen = set()
    unique_entries = []

    for entry in entries:
        key = (entry['word'], entry['reference'])
        if key not in seen:
            seen.add(key)
            unique_entries.append(entry)

    return unique_entries
```

### C. Statistical Validation

After extraction, verify:
- Total entry count
- Unique word count
- Average verses per word
- Length distribution
- Frequency distribution
- No generic words leaked through

---

## 7. SCALABILITY TO 50K

### A. Phase Targets

```python
PHASE_1_TARGET = 40000  # Words freq 2-500
PHASE_2_TARGET = 7000   # Words freq 1
PHASE_3_TARGET = 3000   # Words freq 501-1000

TOTAL_TARGET = 50000
```

### B. Dynamic Adjustment

```python
def adjust_extraction_targets(phase_1_actual):
    """
    If Phase 1 doesn't hit target, adjust other phases
    """
    if phase_1_actual < PHASE_1_TARGET:
        deficit = PHASE_1_TARGET - phase_1_actual

        # Increase Phase 2 (rare words)
        PHASE_2_TARGET += deficit // 2

        # Increase Phase 3 (common words)
        PHASE_3_TARGET += deficit // 2
```

### C. Verses Per Word Calculation

From analysis:
- 8,896 words in 2-500 range
- 40,000 target / 8,896 = 4.5 verses per word
- Average word appears 25.6 times
- **Feasible!** (25.6 >> 4.5)

---

## 8. IMPLEMENTATION WORKFLOW

### A. Extraction Steps

```python
def extract_crossword_entries():
    """
    Main extraction workflow
    """
    # Step 1: Connect to database
    conn = sqlite3.connect(DB_PATH)

    # Step 2: Extract all words with frequencies
    word_freq = build_word_frequency_map(conn)

    # Step 3: Load generic words to exclude
    exclude_list = load_top_frequent_words(word_freq, 200)

    # Step 4: Phase 1 - Core biblical vocabulary (2-500 freq)
    phase_1_entries = extract_phase_1(conn, word_freq, exclude_list)

    # Step 5: Phase 2 - Rare terms (1 freq)
    phase_2_entries = extract_phase_2(conn, word_freq, exclude_list)

    # Step 6: Phase 3 - Common biblical words (501-1000 freq)
    phase_3_entries = extract_phase_3(conn, word_freq, exclude_list)

    # Step 7: Combine and deduplicate
    all_entries = phase_1_entries + phase_2_entries + phase_3_entries
    unique_entries = detect_duplicates(all_entries)

    # Step 8: Validate all entries
    valid_entries = [e for e in unique_entries if validate_entry(**e)]

    # Step 9: Limit to target (if over)
    final_entries = valid_entries[:TOTAL_TARGET]

    # Step 10: Write output
    write_crossword_file(final_entries, OUTPUT_PATH)

    # Step 11: Generate statistics
    generate_extraction_report(final_entries)

    return final_entries
```

### B. Database Query Pattern

```python
def get_verses_for_word(conn, word, max_verses=10):
    """
    Retrieve verses containing a specific word
    """
    cursor = conn.cursor()

    query = """
        SELECT v.text, b.book_name, c.chapter_number, v.verse_number
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        WHERE UPPER(v.text) LIKE ?
        ORDER BY RANDOM()
        LIMIT ?
    """

    cursor.execute(query, (f'%{word}%', max_verses))
    return cursor.fetchall()
```

---

## 9. EXPECTED OUTPUT

### A. File Format

**Filename:** `bible_crossword_50k.txt`

**Structure:**
```
WORD<TAB>none<TAB>clue_text<TAB>reference
WORD<TAB>none<TAB>clue_text<TAB>reference
...
(50,000 lines)
```

### B. Statistics Report

**Filename:** `extraction_report.txt`

**Contents:**
```
EXTRACTION REPORT
=================

Total entries generated: 50,000
Unique words: 12,543
Average verses per word: 3.98

PHASE BREAKDOWN
===============
Phase 1 (2-500 freq):   40,234 entries (8,856 words)
Phase 2 (1 freq):        6,891 entries (6,891 words)
Phase 3 (501-1000 freq): 2,875 entries (112 words)

LENGTH DISTRIBUTION
===================
3 letters:    412 entries
4 letters:  4,234 entries
5 letters:  7,891 entries
6 letters: 10,234 entries
...

FREQUENCY DISTRIBUTION
=====================
1x:        6,891 entries
2-5x:     12,345 entries
6-10x:     8,234 entries
...

QUALITY METRICS
===============
Average clue length: 142 characters
Entries with duplicates: 0
Failed validations: 234
Success rate: 99.5%
```

---

## 10. RISK MITIGATION

### A. Potential Issues

| Issue | Mitigation |
|-------|------------|
| Not enough words for 50K | Include Phase 2 (1x words) + Phase 3 (501-1000x) |
| Too many generic words | Exclude top 200 + manual review |
| Duplicate entries | Hash-based deduplication |
| Poor verse quality | Scoring algorithm for verse selection |
| Special characters | Text cleaning and normalization |
| Database errors | Try-except with logging |

### B. Fallback Strategy

If 50K proves difficult:
1. Lower minimum frequency to 1 (include all words)
2. Increase verses per word to 6-8
3. Include 3-letter words more aggressively
4. Extend frequency range to 1-1000
5. Accept target of 45K instead of 50K (still excellent)

---

## 11. SUCCESS CRITERIA

✅ **50,000 total entries** (±1000 acceptable)
✅ **No generic English words** (top 200 excluded)
✅ **Quality biblical vocabulary** (2-500 freq as primary)
✅ **Proper formatting** (WORD<TAB>none<TAB>clue<TAB>ref)
✅ **No duplicates** (unique word+verse combinations)
✅ **Valid references** (Book Chapter:Verse format)
✅ **Clean text** (no special chars, proper blanking)
✅ **Crossword-friendly lengths** (primarily 4-12 letters)

---

## CONCLUSION

The extraction strategy is **data-driven**, **scalable**, and **achievable**. Analysis shows we have more than sufficient material in the GoodBook.db database to generate 50,000 quality crossword entries. The three-phase approach ensures we prioritize the best biblical vocabulary while having fallback options to reach our target.

**Next Step:** Implement `extract_crossword_entries.py` following this design.
