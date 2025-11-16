# concordance_tools/tag_strongs_entries.py
# This script processes Strong's entries, tagging them based on predefined rules and whitelists.

import os
import json
import re
from collections import defaultdict

INPUT_DIR = "output/concordance"
TAGGED_DIR = "output/tagged"
OUTPUT_DIR = "output/entities"
ENTITY_DIR = "bible_entities"
LOG_FILE = "output/skipped_entries.log"
UNKNOWN_KJV_FILE = "output/unrecognized_kjv_words.json"
os.makedirs(TAGGED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load verified entity whitelists with nested support
ENTITY_LISTS = {}
ALL_KNOWN_WORDS = set()
for filename in os.listdir(ENTITY_DIR):
    if filename.endswith(".json"):
        tag = filename.replace(".json", "").upper()
        with open(os.path.join(ENTITY_DIR, filename), "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if tag in data and isinstance(data[tag], dict):
                    words = set(data[tag].keys())
                else:
                    words = set(data.keys())
                ENTITY_LISTS[tag] = words
                ALL_KNOWN_WORDS.update(words)
            except Exception:
                continue

TAG_RULES = {
    "PERSON": {
        "definition": ["man", "woman", "prophet", "priest"],
        "outline": ["father of", "son of", "wife of", "descendant", "judge"],
        "kjv_translation_count": ["man", "name", "person"],
        "pos": ["proper name"]
    },
    "DEITY": {
        "lemma": ["god", "yhwh", "elohim", "jesus", "christ", "holy spirit"],
        "definition": ["god", "lord", "elohim", "jesus", "christ"],
        "outline": ["god of israel", "name of the lord"]
    },
    "FALSE_GOD": {
        "definition": ["idol", "false god", "heathen deity", "baal"],
        "outline": ["sacrificed to", "worshipped", "phoenician god"],
        "lemma": ["baal", "ashtoreth", "molech"]
    },
    "SPIRITUAL_ENTITY": {
        "definition": ["angel", "spirit", "demon", "devil", "satan", "seraphim"],
        "outline": ["heavenly being", "evil spirit", "sent from god"],
        "kjv_translation_count": ["angel"]
    },
    "CONCEPT": {
        "definition": ["truth", "grace", "faith", "hope", "love", "righteousness", "shame"],
        "outline": ["truth", "grace", "faith", "hope", "love", "righteousness", "shame"]
    }
}

PRIORITY = ["DEITY", "FALSE_GOD", "SPIRITUAL_ENTITY", "PERSON", "CONCEPT"]

skipped_log = []
unknown_kjv = defaultdict(list)

# Load existing unknown words (merge)
if os.path.exists(UNKNOWN_KJV_FILE):
    with open(UNKNOWN_KJV_FILE, "r", encoding="utf-8") as f:
        existing = json.load(f)
        for word, ids in existing.items():
            unknown_kjv[word].extend(ids)

def check_field_for_keywords(text, keywords):
    for word in keywords:
        if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
            return word
    return None

def tag_entry(data):
    matches = {}
    matched_by = {}

    lemma = data.get("lemma", "").strip()
    translit = data.get("transliteration", "").strip().lower()
    strongs_id = data.get("strongs_number")

    if not translit:
        skipped_log.append(f"{strongs_id} skipped: missing transliteration")
        return {"strongs_number": strongs_id, "primary_tag": None}

    # Whitelist matching first
    for tag, known in ENTITY_LISTS.items():
        if translit in known or lemma in known:
            return {
                "strongs_number": strongs_id,
                "lemma": translit,
                "original_form": lemma,
                "primary_tag": tag,
                "matched_by": {tag: ["lemma or transliteration in verified whitelist"]},
                "note": data.get("definition", "")[:180] + "..." if data.get("definition") else ""
            }

    # KJV translation word matching
    kjv_counts = data.get("kjv_translation_count", {})
    if isinstance(kjv_counts, dict):
        for word in kjv_counts:
            w = word.lower()
            for tag, known in ENTITY_LISTS.items():
                if w in known:
                    return {
                        "strongs_number": strongs_id,
                        "lemma": translit,
                        "original_form": lemma,
                        "primary_tag": tag,
                        "matched_by": {tag: [f"kjv_translation_count: {word}"]},
                        "note": data.get("definition", "")[:180] + "..." if data.get("definition") else ""
                    }
            if w not in ALL_KNOWN_WORDS:
                if strongs_id not in unknown_kjv[w]:
                    unknown_kjv[w].append(strongs_id)

    for tag, fields in TAG_RULES.items():
        for field, keywords in fields.items():
            value = data.get(field, "")
            if isinstance(value, list):
                value = " ".join(value)
            value = value.lower()
            word = check_field_for_keywords(value, keywords)
            if word:
                matches[tag] = matches.get(tag, 0) + 1
                matched_by.setdefault(tag, []).append(f"{field}: {word}")

    sorted_tags = sorted(matches.items(), key=lambda x: PRIORITY.index(x[0]) if x[0] in PRIORITY else 99)
    final_tag = sorted_tags[0][0] if sorted_tags else None

    return {
        "strongs_number": strongs_id,
        "lemma": translit,
        "original_form": lemma,
        "primary_tag": final_tag,
        "matched_by": matched_by if final_tag else {},
        "note": data.get("definition", "")[:180] + "..." if data.get("definition") else ""
    }

def build_entity_files():
    entity_store = defaultdict(dict)
    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith(".json"): continue
        with open(os.path.join(INPUT_DIR, filename), "r", encoding="utf-8") as f:
            entry = json.load(f)

        tagged = tag_entry(entry)
        lemma = tagged.get("lemma")
        if not tagged["primary_tag"] or not lemma:
            continue

        tag = tagged["primary_tag"]
        entity_store[tag][lemma] = {
            "default": tag,
            "original_form": tagged.get("original_form", ""),
            "source": tagged.get("strongs_number"),
            "note": tagged.get("note", ""),
            "tag_reasoning": tagged.get("matched_by")
        }

        out_path = os.path.join(TAGGED_DIR, f"{entry['strongs_number']}.json")
        with open(out_path, "w", encoding="utf-8") as out:
            json.dump({**entry, **tagged}, out, indent=2, ensure_ascii=False)

    for tag, entries in entity_store.items():
        with open(os.path.join(OUTPUT_DIR, f"{tag}.json"), "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

    if skipped_log:
        with open(LOG_FILE, "w", encoding="utf-8") as log:
            for line in skipped_log:
                log.write(line + "\n")

    if unknown_kjv:
        with open(UNKNOWN_KJV_FILE, "w", encoding="utf-8") as f:
            json.dump(unknown_kjv, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    build_entity_files()
