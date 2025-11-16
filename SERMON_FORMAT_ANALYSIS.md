# Sermon Transcript Format Analysis & Standardization Plan

**Project:** Chuck Smith Sermon Database for AI Annotation
**Date:** 2025-11-04
**Purpose:** Analyze scraped sermon transcript variations and design standardization process

---

## FILE SAMPLES REVIEWED

1. `A_Time_for_Everything_Part_21__VZUQIs2E.txt`
2. `A_Time_for_Everything_Part_11__utlAenpu.txt`
3. `Divine_Justice1__rVffoZcj.txt`
4. `Destruction_of_the_Midianites92325_04MidianitesPursuing_God_s_PurposeSpiritual_VigilanceNUM_31_9Chuc_P9Fq62O_.txt`
5. `Deuteronomy_5-81__trL5xIFd.txt`

---

## FORMAT VARIATIONS DISCOVERED

### 1. TEXT FORMATTING ISSUES

#### **Problem 1A: Single-Line Files (Critical)**
**File:** `Destruction_of_the_Midianites...txt`
- **Issue:** ENTIRE transcript is ONE LINE with no line breaks
- **Length:** 1 line total
- **Impact:** Impossible to read, parse, or annotate properly
- **Example:** `Oh, let the Son of God enfold you With His Spirit and His love Let Him fill your heart and satisfy your soul Oh, let Him have the things that mold you And His Spirit like a dove Will descend upon your life and make you whole Welcome to The Word for Today Featuring the Bible teaching of Pastor Chuck Smith Of Calvary Chapel, Costa Mesa, California Pastor Chuck is currently leading us on a verse-by-verse study...` [continues for thousands of words]

#### **Problem 1B: Proper Paragraph Formatting (Good)**
**Files:** `A_Time_for_Everything_Part_11`, `Deuteronomy_5-81`
- **Format:** Proper paragraphs with blank lines between
- **Length:** 100-200+ lines
- **Quality:** Clean, readable, annotation-ready
- **Example:**
```
Now, he puts several things into contrast here, some fourteen of them. A time to be born, a time to die, a time to plant, and a time to pluck up that which is planted. A time to kill and a time to heal.

A time to break down, a time to build up. A time to weep, a time to laugh, a time to mourn, a time to dance. A time to cast away stones, a time to gather stones together.
```

#### **Problem 1C: Run-Together Text (Poor)**
**File:** `A_Time_for_Everything_Part_21`
- **Issue:** Text runs together without clear paragraph breaks
- **Impact:** Hard to read, needs cleaning
- **Example:** Sermon text flows directly into promotional content without breaks

---

### 2. CONTENT STRUCTURE ISSUES

#### **Problem 2A: Opening Boilerplate**
**Found in:** Most files

**Pattern 1: Song Lyrics Opening**
```
Oh, let the Son of God enfold you 
With His Spirit and His love 
Let Him fill your heart and satisfy your soul 
Oh, let Him have the things that hold you 
And His Spirit like a dove 
Will descend upon your life And make you whole
```

**Pattern 2: Radio Show Introduction**
```
Welcome to The Word for Today 
Featuring the Bible teaching of Pastor Chuck Smith 
Of Calvary Chapel, Costa Mesa, California 
Pastor Chuck is currently leading us on a verse-by-verse study 
Through the entire Bible 
And on today's edition of The Word for Today 
We'll continue to focus our attention on...
```

**Pattern 3: Chapter/Topic Introduction**
```
Chapter 3, verse 12 
And now with today's message 
Here's Pastor Chuck
```

**Pattern 4: Simple Introduction**
```
And now with today's lesson
Here's Pastor Chuck Smith
```

#### **Problem 2B: Closing Boilerplate**
**Found in:** Most "Word for Today" sermons

**Pattern 1: Subscription Information**
```
We'll return with more of our verse-by-verse study through the book of Ecclesiastes 
In our next lesson as Pastor Chuck Smith continues with Our Attitude Toward God 
And we do hope you'll make plans to join us 
But right now I'd like to remind you that if you'd like to secure a copy of today's message 
Simply order Ecclesiastes chapter 3 verse 12 
When visiting TheWordForToday.org
```

**Pattern 2: Contact Information**
```
While you're there we encourage you to browse the many additional biblical resources by Pastor Chuck 
You can also subscribe to The Word for Today podcast 
Or sign up for our email subscription 
Once again all this can be found at TheWordForToday.org 
If you wish to call our toll-free number is 1-800-272-WORD 
And our office hours are Monday through Friday 8 a.m. to 5 p.m. Pacific Time 
Again that's 1-800-272-9673 
For those of you preferring to write our mailing address is 
The Word for Today, P.O. Box 8000, Costa Mesa, California 92628
```

**Pattern 3: Promotional Content**
```
Have you laid hold of what God has called you to do? 
Well let me ask you this Are you sure you know what your calling is? 
Well ladies I have a special surprise for you 
The Word for Today is making available 
The When Leaders Lead Women's Conference On DVD with a bonus MP3...
```

**Pattern 4: Closing Prayer**
```
And now once again here's Pastor Chuck with today's closing comments 
I pray that God will make this a very special week for you 
That you might follow after the things of the Spirit 
And may you walk in holiness and in purity...
```

**Pattern 5: Program Credits**
```
This program has been sponsored by The Word for Today 
In Costa Mesa, California
```

---

### 3. CONTENT TYPE VARIATIONS

#### **Type A: Standard "Word for Today" Sermon**
- **Files:** Most files
- **Characteristics:**
  - Verse-by-verse Bible teaching
  - Formal sermon structure
  - Radio program format
  - Opening/closing boilerplate
  - Clear scripture focus

#### **Type B: Testimony/Conference Talk**
- **File:** `Divine_Justice1__rVffoZcj.txt`
- **Characteristics:**
  - Personal testimony (9/11 police officer)
  - Conversational, informal style
  - No formal sermon structure
  - No scripture verse-by-verse teaching
  - Very different from sermons
- **Example opening:**
```
Hey, God bless you guys. I thank you for all your prayers and stuff. 
We're really feeling it in New York.
I called my wife up and she told me we had an earthquake in New York. 
You're talking about a bad hair day. I tell you.
```

**⚠️ WARNING:** This is NOT a Chuck Smith sermon - it's someone else's testimony at what appears to be a conference or special event.

---

### 4. FILENAME INCONSISTENCIES

#### **Pattern 1: Clean Names**
- `A_Time_for_Everything_Part_21__VZUQIs2E.txt`
- `A_Time_for_Everything_Part_11__utlAenpu.txt`
- `Divine_Justice1__rVffoZcj.txt`
- `Deuteronomy_5-81__trL5xIFd.txt`

**Format:** `{sermon_title}__{displayRef}.txt`

#### **Pattern 2: Metadata-Heavy Names**
- `Destruction_of_the_Midianites92325_04MidianitesPursuing_God_s_PurposeSpiritual_VigilanceNUM_31_9Chuc_P9Fq62O_.txt`

**Format:** `{title}{date?}{tags?}{scripture?}{speaker?}_{displayRef}.txt`

**Issues:**
- No consistent separator
- Metadata embedded in filename
- Difficult to parse
- Inconsistent naming scheme

---

## STANDARDIZATION REQUIREMENTS

### Phase 1: Text Cleaning

#### **Step 1: Fix Line Breaks**
```python
def fix_line_breaks(text):
    """
    Convert single-line transcripts to proper paragraphs
    
    Strategy:
    - Look for sentence-ending punctuation + space + capital letter
    - Insert newline at natural paragraph breaks
    - Preserve existing paragraph breaks
    """
    # If entire file is one line, add breaks at sentence boundaries
    if '\n' not in text or text.count('\n') < 10:
        # Add breaks after periods followed by capital letters
        text = re.sub(r'(\.) ([A-Z])', r'\1\n\n\2', text)
    return text
```

#### **Step 2: Remove Opening Boilerplate**
```python
def remove_opening_boilerplate(text):
    """
    Remove song lyrics, radio intro, chapter headers
    
    Patterns to remove:
    - Song lyrics (lines with 'enfold', 'Spirit', 'dove', etc.)
    - "Welcome to The Word for Today..."
    - "And now with today's message..."
    - "Here's Pastor Chuck"
    - Chapter/verse references before sermon starts
    """
    # Find actual sermon start (usually after "Here's Pastor Chuck")
    patterns = [
        r'^.*?Here\'s Pastor Chuck\.?\s*',
        r'^.*?And now with today\'s (message|lesson).*?Here\'s Pastor Chuck.*?\n',
        r'^Oh, let the Son of God.*?And make you whole\.?\s*',
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.MULTILINE)
    
    return text.strip()
```

#### **Step 3: Remove Closing Boilerplate**
```python
def remove_closing_boilerplate(text):
    """
    Remove subscription info, contact details, promotional content
    
    Patterns to remove:
    - Everything after "We'll return with more..."
    - Contact information blocks
    - Promotional content
    - Program credits
    """
    # Find sermon end markers
    end_markers = [
        r'We\'ll return with more of our verse-by-verse study.*$',
        r'While you\'re there we encourage you to browse.*$',
        r'If you wish to call our toll-free number.*$',
        r'Have you laid hold of what God has called you to do\?.*$',
        r'This program has been sponsored by.*$',
    ]
    
    for marker in end_markers:
        text = re.sub(marker, '', text, flags=re.DOTALL | re.MULTILINE)
    
    return text.strip()
```

#### **Step 4: Extract Core Sermon**
```python
def extract_core_sermon(text):
    """
    Complete cleaning pipeline
    """
    text = fix_line_breaks(text)
    text = remove_opening_boilerplate(text)
    text = remove_closing_boilerplate(text)
    return text.strip()
```

---

### Phase 2: Metadata Extraction

#### **Metadata to Capture:**

1. **Sermon Identifier**
   - SermonIndex `displayRef` (unique ID)
   - Example: `VZUQIs2E`, `utlAenpu`

2. **Title**
   - Extract from filename or content
   - Example: `A Time for Everything Part 21`

3. **Scripture Reference**
   - Bible book, chapter, verses
   - Example: `Ecclesiastes 3:12-13`

4. **Series Name** (if applicable)
   - Example: `A Time for Everything`, `Word for Today`

5. **Content Type**
   - `sermon` (standard Bible teaching)
   - `testimony` (personal story/experience)
   - `conference` (special event)
   - `other`

6. **Date** (if available)
   - Parse from filename or content
   - Example: `2004-09-23`

7. **Word Count**
   - For quality metrics
   - Example: `3,456 words`

8. **Speaker**
   - Should always be "Chuck Smith" for this collection
   - Flag if different

---

### Phase 3: Database Schema

#### **Recommended SQLite Schema:**

```sql
CREATE TABLE sermons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_ref TEXT UNIQUE NOT NULL,         -- SermonIndex ID
    title TEXT NOT NULL,
    scripture TEXT,                           -- e.g., "Ecclesiastes 3:12-13"
    series TEXT,                              -- Series name if part of series
    content_type TEXT DEFAULT 'sermon',       -- sermon, testimony, conference, other
    speaker TEXT DEFAULT 'Chuck Smith',
    date TEXT,                                -- ISO format: YYYY-MM-DD
    word_count INTEGER,
    
    -- Text content
    raw_transcript TEXT NOT NULL,             -- Original downloaded text
    cleaned_transcript TEXT NOT NULL,         -- After cleaning
    
    -- Processing flags
    has_line_breaks BOOLEAN DEFAULT 0,        -- Original had proper formatting
    had_boilerplate BOOLEAN DEFAULT 0,        -- Had opening/closing material
    needs_review BOOLEAN DEFAULT 0,           -- Flagged for manual review
    
    -- Timestamps
    downloaded_at TEXT,
    processed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sermons_display_ref ON sermons(display_ref);
CREATE INDEX idx_sermons_scripture ON sermons(scripture);
CREATE INDEX idx_sermons_content_type ON sermons(content_type);
CREATE INDEX idx_sermons_series ON sermons(series);
```

---

### Phase 4: Processing Pipeline

#### **Step-by-Step Process:**

```
1. READ raw transcript file
   ↓
2. EXTRACT metadata from filename
   ↓
3. DETECT format issues (single line, etc.)
   ↓
4. CLEAN text (remove boilerplate, fix breaks)
   ↓
5. EXTRACT scripture references
   ↓
6. CLASSIFY content type
   ↓
7. COUNT words
   ↓
8. FLAG for review if needed
   ↓
9. INSERT into database
   ↓
10. VALIDATE and log results
```

---

## QUALITY CONTROL FLAGS

### **Auto-Flag for Manual Review:**

1. **Content Type Issues:**
   - Not a Chuck Smith sermon (different speaker detected)
   - Testimony/conference talk instead of sermon
   - Mixed content types

2. **Formatting Issues:**
   - Word count < 500 (too short)
   - Word count > 20,000 (too long)
   - No scripture references found
   - Single-line format detected

3. **Metadata Issues:**
   - No title extracted
   - Unable to parse scripture reference
   - Filename doesn't match expected pattern

4. **Content Issues:**
   - Excessive boilerplate remaining after cleaning
   - Unusual characters or encoding issues
   - Missing expected sermon elements

---

## PROCESSING SCRIPT OUTLINE

```python
#!/usr/bin/env python3
"""
sermon_standardizer.py

Clean and standardize Chuck Smith sermon transcripts
for database import and AI annotation
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

class SermonStandardizer:
    
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self.create_schema()
    
    def create_schema(self):
        """Create sermons table"""
        # SQL schema from Phase 3
        pass
    
    def process_file(self, file_path: Path) -> Dict:
        """
        Process a single sermon transcript file
        
        Returns:
            metadata dict with all extracted information
        """
        # 1. Read file
        raw_text = file_path.read_text(encoding='utf-8')
        
        # 2. Extract metadata from filename
        metadata = self.extract_metadata_from_filename(file_path.name)
        
        # 3. Detect format issues
        format_issues = self.detect_format_issues(raw_text)
        
        # 4. Clean text
        cleaned_text = self.clean_transcript(raw_text)
        
        # 5. Extract scripture references
        scripture = self.extract_scripture_references(cleaned_text)
        
        # 6. Classify content type
        content_type = self.classify_content_type(cleaned_text)
        
        # 7. Count words
        word_count = len(cleaned_text.split())
        
        # 8. Flag for review
        needs_review = self.should_flag_for_review(
            metadata, format_issues, content_type, word_count
        )
        
        # 9. Compile full metadata
        full_metadata = {
            'display_ref': metadata['display_ref'],
            'title': metadata['title'],
            'scripture': scripture,
            'series': metadata.get('series'),
            'content_type': content_type,
            'speaker': 'Chuck Smith',
            'word_count': word_count,
            'raw_transcript': raw_text,
            'cleaned_transcript': cleaned_text,
            'has_line_breaks': format_issues['has_line_breaks'],
            'had_boilerplate': format_issues['had_boilerplate'],
            'needs_review': needs_review,
            'downloaded_at': metadata.get('downloaded_at'),
            'processed_at': datetime.utcnow().isoformat()
        }
        
        return full_metadata
    
    def clean_transcript(self, text: str) -> str:
        """Clean transcript using Phase 1 methods"""
        text = self.fix_line_breaks(text)
        text = self.remove_opening_boilerplate(text)
        text = self.remove_closing_boilerplate(text)
        return text.strip()
    
    # Additional methods for each processing step...

def main():
    """Process all sermon files"""
    standardizer = SermonStandardizer('sermons.db')
    
    sermon_dir = Path('path/to/sermon/files')
    
    for sermon_file in sermon_dir.glob('*.txt'):
        try:
            metadata = standardizer.process_file(sermon_file)
            standardizer.insert_sermon(metadata)
            print(f"✓ Processed: {sermon_file.name}")
        except Exception as e:
            print(f"✗ Failed: {sermon_file.name} - {e}")
    
    # Print summary statistics
    standardizer.print_summary()

if __name__ == '__main__':
    main()
```

---

## NEXT STEPS

1. **Build the standardizer script** based on outline above
2. **Test on sample files** (these 5 files)
3. **Validate cleaning quality** (manual review of cleaned output)
4. **Process full sermon collection** (~1,537 sermons)
5. **Generate QC report** (flagged items for manual review)
6. **Export clean database** for AI annotation

---

## EXPECTED OUTCOMES

### **After Standardization:**

- ✅ All sermons in consistent format (proper paragraphs)
- ✅ Opening/closing boilerplate removed
- ✅ Metadata extracted and structured
- ✅ Non-sermon content flagged
- ✅ Database ready for AI annotation
- ✅ Quality control report generated

### **Database Statistics:**

- Total sermons: ~1,537
- Expected clean sermons: ~1,400-1,500
- Flagged for review: ~50-100
- Non-sermon content: ~10-20
- Format issues resolved: ~200-300

---

**END OF ANALYSIS**
