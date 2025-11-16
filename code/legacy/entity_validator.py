# entity_validator.py was created to validate and log entities in biblical text using spaCy NLP.
import sqlite3
import json
import os
import re
from collections import defaultdict
import spacy
import string



import logging

class EntityValidator:
    def __init__(self, db_path=None, entity_dir="bible_entities", config_path="config.json", merged_entity_dict=None, verbose=False):
        self.nlp = None  # Lazy-load the NLP model
        self.config_path = config_path
        self.entity_dir = entity_dir
        self.db_path = db_path        
        self.untagged_log = {}
        self.conflicts = {}
        self.logging_dir = "output/LOGS"
        self.entities = {}  # Always initialize as an empty dict

        # Set up logger
        self.logger = logging.getLogger("EntityValidator")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)

        self.load_config()

        # ✅ Support both paths: merged dict or directory
        if merged_entity_dict:
            self.entities = merged_entity_dict
            print(f"✔ Loaded {sum(len(v) for v in merged_entity_dict.values())} entities from merged dictionary.")
        else:
            self.load_flat_entity_dict(self.entity_dir)  # 👈 Make sure this new method exists

        # Create sets for quick access to entity groups
        self.entity_groups = {
            "DEITY": set(k for k, v in self.entities.items() if v.get("default") == "DEITY"),
            "PERSON": set(k for k, v in self.entities.items() if v.get("default") == "PERSON"),
            # Add more groups as needed
        }

    def load_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        if not self.db_path:  # Prioritize constructor argument
            self.db_path = self.config.get("db_path")
        self.logging_dir = self.config.get("logging_dir", "output/LOGS")

    def load_bible_text_from_db(self):
        if not self.db_path:
            raise ValueError("Database path not set in validator.")

        book_name = input("📖 Enter the book name to load text from: ")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
        SELECT v.text
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        WHERE b.book_name = ?
        """
        params = [book_name]

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        self.bible_text = " ".join(row[0] for row in rows if row[0])
        print(f"✔ Loaded Bible text for {book_name} ({len(rows)} verses).")

        # 🧠 Inject entity patterns before running NLP
        self.inject_entity_ruler()

        # 🔍 Run NER and print a quick preview
        if self.nlp is None:
            self.nlp = spacy.load("en_core_web_lg")  # Load NLP model only when needed
        self.doc = self.nlp(self.bible_text)
        print(f"🔎 Found {len(self.doc.ents)} named entities in {book_name}.\n")

        for ent in self.doc.ents[:10]:
            print(f"  - {ent.text} ({ent.label_})")

        # 📝 Optional: log untagged words
        self.log_untagged_words_per_verse(book_name=book_name)

    def load_flat_entity_dict(self, entity_dir):
        """
        Loads and flattens all JSON entity files in the directory into a single flat entity dictionary.
        Supports nested category structures.
        """
        self.entities = {}
        for filename in os.listdir(entity_dir):
            if filename.endswith(".json"):
                path = os.path.join(entity_dir, filename)
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)

                    # Handle nested category format (e.g., "DIVINE_ACTION": { "God said": {...} })
                    for category, entries in data.items():
                        if isinstance(entries, dict):
                            for phrase, config in entries.items():
                                if phrase in self.entities:
                                    print(f"⚠️ Duplicate entity found: {phrase}")
                                self.entities[phrase] = config
        print(f"✔ Loaded {len(self.entities)} total entities from '{entity_dir}'")
    
    def load_all_entities(self):
        for filename in os.listdir(self.entity_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.entity_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        for key, value in data.items():
                            if key not in self.entities:
                                self.entities[key] = {"type": value, "source": filename}
                            else:
                                existing = self.entities[key]
                                self.conflicts[key].append((existing["source"], existing["type"]))
                                self.conflicts[key].append((filename, value))
                    except Exception as e:
                        print(f"Failed to load {filename}: {type(e).__name__} - {str(e)}")
        print(f"✔ Loaded {len(self.entities)} entities from directory.")

    def get_subject_of_token(self, token):
        for child in token.children:
            if child.dep_ == "nsubj":
                return child.text
        return None

    def scan_for_substring_conflicts(self):
        words = set(self.bible_text.split())
        for key in self.entities.keys():
            raw = key.strip()
            for word in words:
                if raw in word and raw != word:
                    self.conflicts.setdefault(raw, set()).add(word)

    def load_entities(self):
        self.entities = {}
        for filename in os.listdir(self.entity_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.entity_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for outer_key, outer_val in data.items():
                            # Check if this is a nested category group (e.g., "SPIRITUAL_ENTITY": { "Abaddon": {...} })
                            if isinstance(outer_val, dict) and all(isinstance(v, dict) for v in outer_val.values()):
                                for entity_name, entity_data in outer_val.items():
                                    if "default" not in entity_data:
                                        entity_data["default"] = outer_key  # Use the group name as the default label
                                    self.entities[entity_name] = entity_data
                            else:
                                # Old flat structure
                                if "default" not in outer_val:
                                    outer_val["default"] = "UNKNOWN"
                                self.entities[outer_key] = outer_val
                except Exception as e:
                    print(f"⚠️ Error loading {filename}: {e}")
        print(f"✔ Loaded {len(self.entities)} total entities from '{self.entity_dir}'\n")

    def log_untagged_words_per_verse(self, book_name):
        self.untagged_log = {
            "book": book_name,
            "verses": {},
            "frequency": []
        }

        if not self.db_path:
            raise ValueError("Database path not set in validator.")

        if not book_name:
            book_name = input("📖 Enter the book name to log untagged words for: ")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
        SELECT b.book_name, c.chapter_number, v.verse_number, v.text
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        WHERE b.book_name = ?
        ORDER BY c.chapter_number, v.verse_number
        """
        cursor.execute(query, (book_name,))
        rows = cursor.fetchall()
        conn.close()

        frequency_dict = {}
        lines = []

        if self.nlp is None:
            self.nlp = spacy.load("en_core_web_lg")

        self.inject_entity_ruler()

        for book, chapter, verse, text in rows:
            doc = self.nlp(text)

            tagged_tokens = set()
            untagged_tokens = set()
            ref = f"{book} {chapter}:{verse}"
            lines.append(f"[{ref}] {text}")

            for token in doc:
                if token.is_stop or token.is_punct or token.is_space:
                    continue  # ✅ Skip common stopwords, punctuation, and spaces

                # Lookup entity from custom entity dictionary
                entity_config = self.lookup_entity(token.text)

                if entity_config:
                    tag = self.apply_contextual_overrides(token, doc, entity_config, ref)
                    tagged_tokens.add(token.text)
                else:
                    untagged_tokens.add(token.text)
                    frequency_dict[token.text] = frequency_dict.get(token.text, 0) + 1

            if untagged_tokens:
                for w in sorted(untagged_tokens):
                    lines.append(f"  - {w}")
            else:
                lines.append("  - All words tagged!")
            
        # At the end of the method, after loop over verses
        self.untagged_log["frequency"] = sorted(
            frequency_dict.items(), key=lambda x: x[1], reverse=True
        )

        # Optionally save it as a JSON for programmatic review
        with open(os.path.join(self.logging_dir, f"{book_name}_untagged.json"), "w", encoding="utf-8") as f:
            json.dump(self.untagged_log, f, indent=2)

        os.makedirs(self.logging_dir, exist_ok=True)
        output_path = os.path.join(self.logging_dir, f"{book_name}_untagged.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"📘 Untagged words per verse saved to {output_path}")   
        
    def save_untagged_log(self, book_name):
        """
        Saves all untagged words (collected by log_untagged_words_per_verse)
        to a JSON file in the configured logging directory.
        """
        output_dir = self.config.get("logging_dir", "output/LOGS")
        os.makedirs(output_dir, exist_ok=True)

        out_path = os.path.join(output_dir, f"{book_name}_untagged.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(self.untagged_log, f, indent=2, ensure_ascii=False)

    def inject_entity_ruler(self):
        """
        Injects custom entities into the spaCy pipeline using EntityRuler.
        It uses the 'default' field in each entity config as the label.
        """
        self.logger.debug("🔁 [DEBUG] inject_entity_ruler() called")

        if self.entities is None or not isinstance(self.entities, dict) or not self.entities:
            raise ValueError("❌ No valid entities loaded into EntityValidator (empty or invalid).")

        # Load NLP model if not already loaded
        if self.nlp is None:
            self.nlp = spacy.load("en_core_web_lg")

        # Remove existing entity_ruler if present to avoid conflicts
        if "entity_ruler" in self.nlp.pipe_names:
            try:
                self.nlp.remove_pipe("entity_ruler")
            except ValueError:
                pass  # Pipeline may have changed; ignore if already removed

        ruler = self.nlp.add_pipe(
            "entity_ruler",
            before="ner",
            config={"overwrite_ents": True},
        )

        patterns = []
        for phrase, config in self.entities.items():
            label = config.get("default", "UNKNOWN")
            patterns.append({"label": label, "pattern": phrase})

        if not patterns:
            print("⚠️ No patterns found to inject into EntityRuler.")
        else:
            try:
                ruler.add_patterns(patterns)
                print(f"✔ Injected {len(patterns)} patterns into spaCy EntityRuler.")
            except Exception as e:
                print(f"❌ Error adding patterns to EntityRuler: {e}")

    def print_conflict_report(self):
        print("\n🔎 [Validator Report]")
        if not self.conflicts:
            print("✅ No substring conflicts found.")
            return

        for raw_key, conflicts in self.conflicts.items():
            print(f"⚠️ Entity '{raw_key}' found inside:")
            for c in sorted(conflicts):
                print(f"   - {c}")

    def save_conflicts_log(self, output_path="conflict_log.json"):
        serializable_conflicts = {
            k: list(v) if isinstance(v, set) else v for k, v in self.conflicts.items()
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(serializable_conflicts, f, indent=4)
        print(f"📝 Conflict log saved to {output_path}")

    def lookup_entity(self, text):

        """
        Looks up an entity configuration by:
        1. Exact match (case-sensitive)
        2. Case-insensitive match
        3. Multi-word phrase match
        Returns entity config dict or None.
        """
        # 1. Exact match
        if text in self.entities:
            #print(f"[lookup_entity] ✅ Exact match: '{text}'")
            return self.entities[text]

        # 2. Case-insensitive fallback
        lowered = text.lower()
        for key in self.entities:
            if key.lower() == lowered:
                #print(f"[lookup_entity] 🔄 Case-insensitive match: '{text}' → '{key}'")
                return self.entities[key]

        # 3. Phrase match
        if " " in text:
            words = text.split()
            phrase_candidates = [k for k in self.entities if " " in k]
            for phrase in phrase_candidates:
                if phrase.lower() == text.lower():
                    #print(f"[lookup_entity] 🧠 Phrase match: '{text}' → '{phrase}'")
                    return self.entities[phrase]

        #print(f"[lookup_entity] ❌ No match: '{text}'")
        return None
    
    def apply_contextual_overrides(self, token, doc, entity_config, verse_ref=None):

        """
        Applies contextual overrides based on the token and sentence text.
        This method checks if the token's subject matches any known entities
        and returns the appropriate action type based on the entity configuration.
        """
        
        # ✅ Book-specific override (e.g., "Genesis 1")
        if verse_ref and "rules" in entity_config:
            for key, rule in entity_config["rules"].items():
                if verse_ref.startswith(key):  # e.g., "Genesis 1" in "Genesis 1:6"
                    override = rule.get("override")
                    if override:
                        return override

        # If no entity config, return default
        subject = None

        # Find matching token in the sentence
        for t in doc:
            if t.text.lower() == token.text.lower():
                subject = self.get_subject_of_token(t)
                break

        if subject:
            subject_lower = subject.lower()
            if subject_lower in (name.lower() for name in self.entity_groups.get("DEITY", [])):
                return "DIVINE_ACTION"
            elif subject_lower in (name.lower() for name in self.entity_groups.get("PERSON", [])):
                return "HUMAN_ACTION"
            # You can add more elifs for PROPHET, TITLE, etc.



        return entity_config.get("default", "OTHER")
    
    def evaluate_override_condition(self, condition: str, token, sentence_text) -> bool:
        condition = condition.strip()

        # 🔍 Step 1: Find subject of the token
        subject = None
        for possible in token.doc:
            if possible.dep_ == "nsubj" and possible.head == token:
                subject = possible.text
                break

        # Debug: Show what we found
        print(f"[DEBUG] Evaluating condition: '{condition}' for verb: '{token.text}' | Subject found: '{subject}'")

        if not subject:
            return False  # No subject found, can't evaluate

        # 🔄 Step 2: Normalize the subject
        normalized = " ".join(w for w in subject.lower().split() if w not in {"the", "a", "an"})

        # 🔍 Step 3: Apply known override logic
        if condition == "if subject NOT IN DEITY":
            deity_list = self.entity_groups.get("DEITY", set())
            return normalized not in {d.lower() for d in deity_list}

        if condition == "if subject IN DEITY":
            deity_list = self.entity_groups.get("DEITY", set())
            return normalized in {d.lower() for d in deity_list}

        # ❓ Placeholder for future rules
        # elif condition.startswith("if subject IN ["):
        #     ...

        return False
    
    def extract_subject(self, doc, verb_token):
        """Find the likely subject for a given verb."""
        for token in doc:
            if token.dep_ == "nsubj" and token.head == verb_token:
                return token.text
        return None