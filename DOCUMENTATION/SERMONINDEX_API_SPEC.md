# SermonIndex API Specification

**Source:** SermonIndex.net Public Domain API  
**License:** CC0 / Public Domain  
**Documentation:** https://github.com/sermonindex/audio_api  

---

## API ENDPOINTS

### Base URLs

SermonIndex provides two endpoints for accessing their static JSON API:

```
GitHub (Recommended):
https://raw.githubusercontent.com/sermonindex/audio_api/master/

SermonIndex Direct:
http://api.sermonindex.net/audio/
```

### Available Endpoints

1. **Speaker Index** - List all available speakers
2. **Speaker Sermons** - Get all sermons for a specific speaker
3. **Scripture Index** - Browse by Bible book
4. **Topic Index** - Browse by topic/theme

---

## 1. SPEAKER INDEX

### Endpoint
```
GET https://raw.githubusercontent.com/sermonindex/audio_api/master/speaker/_sermonindex.json
```

### Response Structure
```json
{
  "speaker_code": "/speaker/speaker_code.json",
  "chuck_smith": "/speaker/chuck_smith.json",
  "leonard_ravenhill": "/speaker/leonard_ravenhill.json",
  ...
}
```

### Fields
- **speaker_code** (string): Lowercase identifier with underscores
- **path** (string): Relative path to the speaker's sermon JSON file

### Example Response (Partial)
```json
{
  "a_paget_wilkes": "/speaker/a_paget_wilkes.json",
  "aaron_clark": "/speaker/aaron_clark.json",
  "aw_tozer": "/speaker/aw_tozer.json",
  "brian_brodersen": "/speaker/brian_brodersen.json",
  "chuck_missler": "/speaker/chuck_missler.json",
  "chuck_smith": "/speaker/chuck_smith.json"
}
```

**Total Speakers:** ~3,000+ speakers in the index

---

## 2. SPEAKER SERMONS LIST

### Endpoint
```
GET https://raw.githubusercontent.com/sermonindex/audio_api/master/speaker/{speaker_code}.json
```

### Example for Chuck Smith
```
GET https://raw.githubusercontent.com/sermonindex/audio_api/master/speaker/chuck_smith.json
```

### Response Structure
The response is an array of sermon objects:

```json
[
  {
    "title": "Sermon Title Here",
    "subtitle": "Optional subtitle or series name",
    "scripture": "John 3:16-21",
    "speaker": "Chuck Smith",
    "topic": "Grace, Salvation, Gospel",
    "notes": "Additional sermon notes or description",
    "lang_id": "1",
    "displayRef": "unique_sermon_id_or_slug",
    "downloadCount": "1234",
    "playCount": "5678",
    "duration": "45:32",
    "size": "10.5 MB",
    "sourceId": "273",
    "catId": "273"
  },
  ...
]
```

### Fields Description

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | string | Main sermon title | "(People God Uses) 01 the People Used by God" |
| `subtitle` | string | Subtitle or series name | "People God Uses" |
| `scripture` | string | Bible reference(s) | "1CO 3:6" or "Matt 5:1-12" |
| `speaker` | string | Speaker name | "Chuck Smith" |
| `topic` | string | Topics/themes (comma-separated) | "Grace, Salvation, Gospel" |
| `notes` | string | Sermon description/summary | "In this sermon..." |
| `lang_id` | string | Language ID (1 = English) | "1" |
| `displayRef` | string | Unique sermon identifier/slug | "baE8S_E03sl0gb12" |
| `downloadCount` | string | Number of downloads | "1234" |
| `playCount` | string | Number of plays | "5678" |
| `duration` | string | Audio length (MM:SS or HH:MM:SS) | "45:32" |
| `size` | string | File size (with units) | "10.5 MB" or "32K" |
| `sourceId` | string | Source category ID | "273" |
| `catId` | string | Category ID | "273" |

### Notes on Fields
- Not all fields are present in every sermon
- Some sermons may have empty strings for certain fields
- `displayRef` is the key field for constructing the sermon page URL
- Scripture references use various formats (OSIS codes, abbreviations)

---

## 3. INDIVIDUAL SERMON PAGE

### URL Pattern
```
https://www.sermonindex.net/sermons/{displayRef}
```

### Example
```
https://www.sermonindex.net/sermons/baE8S_E03sl0gb12
```

### Available on Sermon Page

1. **Full Transcript** (HTML)
   - Available in the page content
   - Wrapped in sermon transcript section

2. **Download Links**
   - MP3 audio file
   - TXT transcript (plain text)
   - PDF transcript
   - SRT subtitles (if available)
   - VTT subtitles (if available)

3. **Metadata**
   - Speaker bio
   - Scripture references
   - Topics/tags
   - Series information
   - Play count
   - Duration

### Transcript Extraction
The transcript is embedded in the HTML page. Common patterns:
- Within specific div/section tags
- May include timestamps
- Usually clean, well-formatted text
- Some sermons may not have transcripts

---

## 4. SCRIPTURE INDEX

### Endpoint
```
GET https://raw.githubusercontent.com/sermonindex/audio_api/master/scripture/_sermonindex.json
```

### Response Structure
```json
{
  "genesis": "/scripture/genesis.json",
  "exodus": "/scripture/exodus.json",
  "matthew": "/scripture/matthew.json",
  ...
}
```

### Book-Specific Sermons
```
GET https://raw.githubusercontent.com/sermonindex/audio_api/master/scripture/john/_sermonindex.json
```

Returns all sermons tagged with references from that Bible book.

---

## 5. TOPIC INDEX

### Endpoint
```
GET https://raw.githubusercontent.com/sermonindex/audio_api/master/topic/_sermonindex.json
```

### Response Structure
```json
{
  "grace": "/topic/grace.json",
  "salvation": "/topic/salvation.json",
  "prayer": "/topic/prayer.json",
  ...
}
```

---

## CHUCK SMITH SPECIFIC DATA

### Total Sermons
Based on SermonIndex speaker page: **~1,537 sermons**

### Common Series
- "The Word for Today" (expositional teaching)
- "People God Uses"
- "Calvary Chapel distinctives"
- Through-the-Bible teaching series

### Typical Metadata
- Scripture: Usually includes book/chapter/verse references
- Topics: Often includes themes like "Expositional", "Teaching", "Grace"
- Duration: Ranges from 25-60 minutes typically
- Format: MP3 audio + text transcripts for most sermons

### Sample Chuck Smith Sermon Object
```json
{
  "title": "(The Word for Today) Isaiah 10:5 - Part 3",
  "subtitle": "Expositional",
  "scripture": "ISA 10:5, ISA 11:1, JER 2:13",
  "speaker": "Chuck Smith",
  "topic": "Expositional",
  "notes": "In this sermon, Pastor Chuck Smith discusses the warnings given by the prophet Jeremiah...",
  "lang_id": "1",
  "displayRef": "unique_id_here",
  "downloadCount": "456",
  "playCount": "789",
  "duration": "25:59",
  "size": "8.1K",
  "sourceId": "273",
  "catId": "273"
}
```

---

## DATA QUALITY NOTES

### Strengths
✅ Clean, structured JSON format  
✅ Comprehensive metadata (scripture, topics, duration)  
✅ Transcripts available for most sermons  
✅ Public domain/CC0 license  
✅ Well-maintained API (updated monthly)  
✅ Rate limiting not enforced (but requested to be respectful)

### Limitations
⚠️ Not all sermons have transcripts  
⚠️ Some metadata fields may be empty  
⚠️ Scripture references use mixed formats (OSIS codes + abbreviations)  
⚠️ Download counts/play counts are strings, not integers  
⚠️ File sizes include units in the string ("10.5 MB")

### Recommended Scraping Strategy
1. Use GitHub endpoint (more reliable than SermonIndex direct)
2. Rate limit: 2 seconds between requests (respectful)
3. Handle missing transcripts gracefully
4. Parse scripture references carefully (mixed formats)
5. Store both metadata and transcripts
6. Track progress for resume capability

---

## LEGAL & ETHICAL CONSIDERATIONS

### License
SermonIndex states on their site:
> "All sermons are offered freely and all contents of the site where applicable 
> is committed to the public domain for the free spread of the gospel."

This is effectively CC0 (Creative Commons Zero) - public domain dedication.

### Permitted Uses
✅ Download and store locally  
✅ Redistribute freely  
✅ Create derivative works  
✅ Commercial use  
✅ No attribution required (though recommended)

### Best Practices
- Be respectful with rate limiting (2+ seconds between requests)
- Cite SermonIndex as the source
- Consider cloning their GitHub repo instead of hitting API repeatedly
- Update monthly (they recommend `git pull origin master`)

---

## IMPLEMENTATION NOTES

### Recommended Flow

1. **Discovery Phase**
   ```python
   # Get speaker index
   speakers = fetch_json("speaker/_sermonindex.json")
   
   # Find target speaker
   chuck_smith_path = speakers["chuck_smith"]  # "/speaker/chuck_smith.json"
   ```

2. **Enumeration Phase**
   ```python
   # Get all sermons for speaker
   sermons = fetch_json("speaker/chuck_smith.json")
   
   # Process each sermon
   for sermon in sermons:
       sermon_id = sermon["displayRef"]
       title = sermon["title"]
       scripture = sermon.get("scripture", "")
       # ... store metadata
   ```

3. **Download Phase**
   ```python
   # For each sermon, fetch the sermon page
   url = f"https://www.sermonindex.net/sermons/{sermon_id}"
   html = fetch_html(url)
   
   # Extract transcript from HTML
   transcript = parse_transcript(html)
   
   # Download audio (optional)
   mp3_url = extract_mp3_link(html)
   download_file(mp3_url)
   ```

### Error Handling
- Handle missing fields gracefully (use `.get()` with defaults)
- Catch network timeouts (30-second timeout recommended)
- Log failed downloads for retry
- Validate transcript length (>100 chars minimum)

### Progress Tracking
- Save completed sermon IDs to JSON
- Save failed sermon IDs separately
- Enable resume capability
- Save overall progress summary

---

## EXAMPLE USAGE

### Python with Requests
```python
import requests
import time

BASE_URL = "https://raw.githubusercontent.com/sermonindex/audio_api/master"

# Get Chuck Smith sermons
response = requests.get(f"{BASE_URL}/speaker/chuck_smith.json", timeout=30)
sermons = response.json()

print(f"Found {len(sermons)} Chuck Smith sermons")

# Rate limiting
time.sleep(2)

# Process first sermon
first_sermon = sermons[0]
print(f"Title: {first_sermon['title']}")
print(f"Scripture: {first_sermon.get('scripture', 'N/A')}")
print(f"Duration: {first_sermon.get('duration', 'N/A')}")
```

---

## APPENDIX: OSIS SCRIPTURE CODES

SermonIndex uses OSIS (Open Scripture Information Standard) codes in scripture fields:

**Old Testament:**
GEN, EXO, LEV, NUM, DEU, JOS, JDG, RUT, 1SA, 2SA, 1KI, 2KI, 1CH, 2CH, EZR, NEH, EST, JOB, PSA, PRO, ECC, SNG, ISA, JER, LAM, EZK, DAN, HOS, JOL, AMO, OBA, JON, MIC, NAM, HAB, ZEP, HAG, ZEC, MAL

**New Testament:**
MAT, MRK, LUK, JHN, ACT, ROM, 1CO, 2CO, GAL, EPH, PHP, COL, 1TH, 2TH, 1TI, 2TI, TIT, PHM, HEB, JAS, 1PE, 2PE, 1JN, 2JN, 3JN, JUD, REV

---

**END OF SPECIFICATION**
