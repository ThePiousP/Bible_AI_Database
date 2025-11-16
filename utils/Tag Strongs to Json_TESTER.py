# Tag Strongs to Json.py
import os
import json
import sqlite3
from collections import defaultdict
import re
import unicodedata

# =========================
# CONFIG & PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Optional config.json (lets you override dirs)
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
CONFIG = {}
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as _cf:
            CONFIG = json.load(_cf)
    except Exception as e:
        print(f"⚠️ Could not read config.json: {e}")

# Prefer explicit concordance DB path; else default to local file
db_path = CONFIG.get("concordance_db_path", os.path.join(BASE_DIR, "concordance.db"))
resolved_db = os.path.abspath(db_path)

# Entity dir and output dir (project‑relative defaults)
entity_dir = CONFIG.get("entity_dir", os.path.join(BASE_DIR, "bible_entities"))
output_root = CONFIG.get("output_dir", os.path.join(BASE_DIR, "output", "data"))
output_dir = os.path.join(output_root, "bible_entities_output")
os.makedirs(output_dir, exist_ok=True)

skipped_log = os.path.join(output_dir, "skipped_entries.txt")
debug_log = os.path.join(output_dir, "debug_log.txt")
ambiguous_path = os.path.join(output_dir, "ambiguous.json")
whitelist_dir = entity_dir  # nested entity JSONs live here

# Fail fast if DB missing or table absent
if not os.path.exists(resolved_db):
    raise FileNotFoundError(f"❌ Database not found at: {resolved_db}")
print(f"📦 Using database: {resolved_db}")

with sqlite3.connect(resolved_db) as _conn:
    _cur = _conn.cursor()
    _cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    _tables = {r[0] for r in _cur.fetchall()}
    if "concordance_entries" not in _tables:
        raise RuntimeError(
            "❌ Expected table 'concordance_entries' not found.\n"
            f"   Tables present: {sorted(_tables)}\n"
            "   If your table name differs, tell me and I’ll adapt the SELECT."
        )

# =========================
# Name normalization (for matching only; output preserves casing)
# =========================
def strip_accents(s: str) -> str:
    if not isinstance(s, str):
        s = str(s) if s is not None else ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def normalize_key(s: str) -> str:
    """
    Build a normalized key for robust matching across:
    - case (lowercase),
    - spaces / hyphens / underscores / em/en dashes (removed),
    - apostrophes/quotes (removed),
    - simple alias: 'yahweh' -> 'jehovah' at the beginning to fold transliterations.
    Examples (all -> 'jehovahjireh'):
      'Jehovah Jireh', 'Jehovah-Jireh', 'JEHOVAH JIREH', 'Jehovahjireh', 'Yahweh Yireh'
    """
    s = strip_accents(s)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    # Lowercase early so aliasing is easy
    s = s.lower()
    # Map transliteration at the start (optional, helps Yahweh → Jehovah family)
    s = re.sub(r"^yahweh", "jehovah", s)
    # Remove separators and punctuation commonly used in divine names
    s = re.sub(r"[\s_\-\u2010-\u2015]+", "", s)  # spaces/underscores/hyphens/dashes
    s = re.sub(r"[\"'.,;:!?()\[\]{}]", "", s)   # quotes & punctuation
    return s

# =========================
# WHITELISTS (nested, with canonical case + normalized lookup)
# =========================
WHITELIST_TAGS = ["BIBLE_FLORA", "BIBLE_NATIONS", "DEITY", "TIME"]

# LOOKUP by normalized key:  { TAG: set(norm_key) }
WHITELIST_LOOKUP_NORM = {tag: set() for tag in WHITELIST_TAGS}
# CANONICAL name map by normalized key: { TAG: { norm_key: OriginalCasedName } }
WHITELIST_CANONICAL = {tag: {} for tag in WHITELIST_TAGS}

def load_nested_names(tag_name: str):
    """Load {tag: {Name: {...}}} preserving original casing, plus normalized lookup keys."""
    path = os.path.join(whitelist_dir, f"{tag_name}.json")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        group = data.get(tag_name, {})
        if isinstance(group, dict):
            for name in group.keys():
                norm = normalize_key(name)
                WHITELIST_LOOKUP_NORM[tag_name].add(norm)
                # Keep first-seen canonical casing (your files are authoritative)
                WHITELIST_CANONICAL[tag_name].setdefault(norm, name)
    except Exception as e:
        print(f"❌ Failed to load whitelist {path}: {e}")

for _tag in WHITELIST_TAGS:
    load_nested_names(_tag)

# =========================
# Strict DEITY allow‑list (extended from DEITY.json, normalized)
# =========================
BASE_DEITY_ALLOW = {
    "yhwh", "yahweh", "jehovah", "godthefather",
    "jesus", "jesuschrist", "christjesus", "thechrist",
    "holyspirit", "spiritofgod", "spiritofthelord",
}
DEITY_ALLOW = set(BASE_DEITY_ALLOW)
for norm_name in WHITELIST_LOOKUP_NORM.get("DEITY", set()):
    DEITY_ALLOW.add(norm_name)

# =========================
# Tagging rules (your approved set; PERSON pronouns removed)
# =========================
TAG_RULES = {
    "PERSON": {
        "required_fields": [("definition", "part_of_speech"), ("outline", "part_of_speech")],
        "keywords": {
            "definition": ["man", "woman", "prophet", "priest"],
            "outline": ["father of", "son of", "wife of", "descendant", "judge"],
            "part_of_speech": [
                "proper masculine noun",
                "proper feminine noun",
                "proper gentilic noun",
                "proper noun with reference to people",
            ],
        },
    },
    "PROPHET": {
        "required_fields": [("definition", "outline")],
        "keywords": {
            "definition": ["prophet"],
            "outline": ["the prophet", "seer"],
            "part_of_speech": ["proper masculine noun"],
        },
    },
    # Minimal DEITY rule; final decision enforced by strict allow‑list above
    "DEITY": {
        "required_fields": [("definition", "outline")],
        "keywords": {
            "definition": ["jesus", "christ", "holy spirit"],
            "outline": ["name above every name", "spirit of god"],
            "part_of_speech": ["proper noun with reference to deity"],
        },
    },
    "FALSE_GOD": {
        "required_fields": [("definition", "outline")],
        "keywords": {
            "definition": ["idol", "false god", "heathen deity"],
        },
    },
    "SPIRITUAL_ENTITY": {
        "required_fields": [("definition", "outline"), ("definition", "kjv_translation_count")],
        "keywords": {
            "definition": ["angel", "spirit", "demon", "devil", "satan"],
            "outline": ["evil spirit", "heavenly being"],
            "kjv_translation_count": ["angel"],
        },
    },
    "CONCEPT": {
        "required_fields": [("definition", "part_of_speech"), ("definition", "outline")],
        "keywords": {
            "definition": ["truth", "grace", "faith", "love", "hope", "righteousness"],
            "outline": ["truth", "grace", "faith", "hope"],
            "part_of_speech": ["noun abstract", "noun common", "adjective", "verbal noun"],
        },
    },
    "LOCATION": {
        "required_fields": [("definition", "outline"), ("part_of_speech", "outline")],
        "keywords": {
            "definition": ["city", "village", "region", "mountain", "valley", "place", "country", "land"],
            "outline": ["in the land of", "dwelt in", "a city of", "border of", "region of"],
            "part_of_speech": [
                "proper locative noun",
                "proper feminine locative noun",
                "proper noun with reference to territory",
                "proper noun with reference to a mountain",
                "proper noun with reference to a river",
            ],
        },
    },
    "TIME": {
        "required_fields": [("definition", "outline"), ("definition", "part_of_speech")],
        "keywords": {
            "definition": ["day", "month", "sabbath", "evening", "hour", "season", "time"],
            "outline": ["appointed time", "hour of", "season of", "in that day"],
            "part_of_speech": ["temporal noun"],
        },
    },
    "BIBLE_FLORA": {
        "required_fields": [("definition", "outline")],
        "keywords": {
            "definition": ["cedar", "olive", "myrtle", "fig", "vine", "palm", "almond"],
            "outline": ["tree", "plant"],
        },
    },
    "BIBLE_ANIMALS": {
        "required_fields": [("definition", "outline")],
        "keywords": {
            "definition": ["lion", "lamb", "goat", "sheep", "bull", "camel", "donkey"],
            "outline": ["beast", "creature"],
        },
    },
    "NUMERIC": {
        "required_fields": [("definition", "kjv_translation_count")],
        "keywords": {
            "definition": ["one", "two", "three", "four", "five", "ten", "hundred", "thousand"],
            "kjv_translation_count": ["one", "two", "three", "four", "five", "ten"],
        },
    },
    "FUNCTION": {
        "required_fields": [("definition", "part_of_speech")],
        "keywords": {
            "definition": ["again", "only", "even", "up", "down", "on", "in"],
            "part_of_speech": ["adverb", "preposition"],
        },
    },
}

# =========================
# Helpers (KJV parsing) — NEVER lowercase tokens for output
# =========================
def clean_kjv_word(word):
    if not isinstance(word, str):
        word = str(word) if word is not None else ""
    # normalize punctuation variants but DO NOT change case
    word = word.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    word = word.replace("–", "-").replace("—", "-")
    word = re.sub(r"\s+", " ", word)
    word = re.sub(r"\([^)]*\)", "", word)          # drop parenthetical counts/hints
    word = re.sub(r"(with [HG]\d+)", "", word, flags=re.I)
    word = word.strip().strip('".,;:')
    return word

def extract_kjv_words(raw_text):
    if not raw_text:
        return []
    # e.g., "Word (12x), Other (1x)"
    matches = re.findall(r"([A-Za-z][A-Za-z\s\-\'\(\)]*)\s*\(\d+x\)", raw_text)
    cleaned = [clean_kjv_word(m) for m in matches if clean_kjv_word(m)]
    if cleaned:
        return cleaned
    tokens = re.split(r"[\.,;\n]", raw_text)
    return [clean_kjv_word(tok) for tok in tokens if clean_kjv_word(tok)]

def match_fields(entry, keywords):
    """Keyword presence by field (case-insensitive search), output casing untouched."""
    fields_matched = set()
    reasoning = []
    for field, words in keywords.items():
        val = entry.get(field, "")
        if isinstance(val, list):
            val = " ".join(val)
        if isinstance(val, str):
            low = val.lower()
            for w in words:
                if w.lower() in low:
                    fields_matched.add(field)
                    reasoning.append(f"Matched '{w}' in '{field}'")
    return fields_matched, reasoning

def eval_rules(entry):
    """
    Returns a tuple:
      accepted: { TAG: [reasons...] }  (meets any required pair)
      ambiguous: { TAG: [reasons..., 'score=N'] } (>=1 field matched but not accepted)
    """
    accepted, ambiguous = {}, {}
    for tag, rule in TAG_RULES.items():
        matched_fields, reasoning = match_fields(entry, rule["keywords"])
        score = len(matched_fields)
        confident = any(all(f in matched_fields for f in pair) for pair in rule.get("required_fields", []))
        if confident:
            accepted[tag] = reasoning + [f"score={score}"]
        elif score >= 1:
            ambiguous[tag] = reasoning + [f"score={score}"]
    return accepted, ambiguous

# =========================
# Main
# =========================
conn = sqlite3.connect(resolved_db)
cursor = conn.cursor()
cursor.execute("SELECT * FROM concordance_entries")
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]

# nested output accumulator: { TAG: { CanonicalName: { ... } } }
tags_out = defaultdict(dict)
# ambiguous accumulator (nested): { TAG: { CanonicalName: [reasons...] } }
ambiguous_out = defaultdict(lambda: defaultdict(list))

total_processed = 0
unknown_count = 0

# Clear logs each run
for logp in (skipped_log, debug_log):
    try:
        if os.path.exists(logp):
            os.remove(logp)
    except Exception:
        pass

for row in rows:
    total_processed += 1
    entry = dict(zip(columns, row))
    raw = entry.get("kjv_translation_count", "")
    words = extract_kjv_words(raw)

    # candidate word from KJV list (preserve casing)
    canonical_name = None
    last_seen = None

    # 1) Try whitelist match using NORMALIZED keys (recovers canonical casing from file)
    for w in words:
        cand = w.strip()
        if not cand:
            continue
        last_seen = cand
        norm = normalize_key(cand)
        hit_tag = None
        for tag, lookup_norm in WHITELIST_LOOKUP_NORM.items():
            if norm in lookup_norm:
                hit_tag = tag
                canonical_name = WHITELIST_CANONICAL[tag][norm]  # exact casing from entity file
                break
        if canonical_name:
            break

    # 2) Fallback to last seen token (still preserve its original case)
    if not canonical_name:
        canonical_name = last_seen if last_seen else f"UNKNOWN_{entry.get('strongs_number')}"

    if isinstance(canonical_name, str) and canonical_name.startswith("UNKNOWN"):
        unknown_count += 1
        with open(skipped_log, "a", encoding="utf-8") as log:
            log.write(f"{entry.get('strongs_number')} | No English match | Raw: {raw}\n")

    # Decide tags: whitelist beats rules
    accepted, weak_hits = {}, {}
    whitelisted = False
    if not canonical_name.startswith("UNKNOWN"):
        # Use normalized key for allow‑list/whitelist checks
        norm_name = normalize_key(canonical_name)
        for tag, lookup_norm in WHITELIST_LOOKUP_NORM.items():
            if norm_name in lookup_norm:
                accepted[tag] = [f"Whitelisted in {tag}", "score=N/A"]
                whitelisted = True
                break

    if not whitelisted:
        accepted, weak_hits = eval_rules(entry)

    # Strict DEITY allow‑list (normalized): demote non-allowed DEITY to ambiguous
    if "DEITY" in accepted:
        norm_name = normalize_key(canonical_name)
        if norm_name not in DEITY_ALLOW:
            reasons = accepted.pop("DEITY")
            ambiguous_out["DEITY"][canonical_name].extend(reasons + ["demoted_by_allow_list=true"])

    # Debug log
    try:
        with open(debug_log, "a", encoding="utf-8") as log:
            log.write(
                f"Processed {entry.get('strongs_number')} | Word: {canonical_name} | "
                f"Tags: {list(accepted.keys())} | Weak: {list(weak_hits.keys())} | "
                f"POS: {entry.get('part_of_speech')} | Raw KJV: {raw}\n"
            )
    except Exception as e:
        print(f"⚠️ Failed writing debug log: {e}")

    # Collect accepted tags (NESTED, with exact original capitalization)
    for tag, reasons in accepted.items():
        tags_out[tag][canonical_name] = {
            "default": tag,
            "note": f"Auto-tagged from Strong's {entry.get('strongs_number')}",
            "source": entry.get('strongs_number'),
            "tag_reasoning": reasons,
        }

    # Collect ambiguous (sub‑threshold) hits for triage (NESTED, preserve name casing)
    for tag, reasons in weak_hits.items():
        ambiguous_out[tag][canonical_name].extend(reasons)

# =========================
# Write outputs
# =========================
for tag, data in tags_out.items():
    out_path = os.path.join(output_dir, f"{tag}.json")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({tag: data}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Failed writing {out_path}: {e}")

# Save ambiguous candidates, if any
if any(ambiguous_out.values()):
    try:
        with open(ambiguous_path, "w", encoding="utf-8") as f:
            json.dump(ambiguous_out, f, indent=2, ensure_ascii=False)
        print(f"🟡 Ambiguous candidates saved to {ambiguous_path}")
    except Exception as e:
        print(f"⚠️ Failed writing ambiguous output: {e}")

print(f"✅ Tagging complete. {len(tags_out)} tag files written to {output_dir}.")
print(f"🟡 Ambiguous tags collected for {sum(bool(v) for v in ambiguous_out.values())} categories.")
print(f"🔎 Total entries processed: {total_processed} | Unknown: {unknown_count}")
