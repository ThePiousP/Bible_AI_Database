# Bible Scraper version: 0.981
# This code provides a command-line interface for scraping, converting, inserting into a database,
# and performing AI-related tasks on Bible texts. It includes menus for different functionalities
# and integrates with other modules like BibleScraper and EntityValidator.

import os
import logging
from bible_scraper import BibleScraper  # Importing BibleScraper class
from entity_validator import EntityValidator  # Importing EntityValidator class for NER validation
import json


# Instantiate BibleScraper
scraper = BibleScraper()

# Pull config from scraper
CONFIG = scraper.config
OUTPUT_DIR = CONFIG.get("output_dir", "output")
DEBUG_MODE = CONFIG.get("debug_mode", True)
CLEANUP_MODE = CONFIG.get("cleanup_mode", True)
BIBLE_VERSION = CONFIG.get("bible_version", "NKJV")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Setup logging
LOG_FILE = os.path.join(OUTPUT_DIR, "debug.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG if DEBUG_MODE else logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def main_menu():
    while True:
        print(f"\n==== AARON'S GAME [Scraper v{scraper.config.get('version', '0.983')}] ====")
        print("\n===== MAIN MENU =====")
        print("1. Scraping & Conversion")
        print("2. Database Insertion")
        print("3. AI Development")
        print("9. Debug Tools")
        print("0. Exit")
        choice = input("Select an option: ").strip()

        if choice == "1":
            scraping_conversion_menu()
        elif choice == "2":
            database_insertion_menu()
        elif choice == "3":
            ai_development_menu()
        elif choice == "9":
            ai_debug_menu()
        elif choice == "0":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Try again.")

def scraping_conversion_menu():
    while True:
        print("\n== Scraping & Conversion Menu ==")
        print("1. Bible Scraper Menu")
        print("2. Concordance Scraper Menu")
        print("")
        print("0. Back")
        choice = input("Select an option: ").strip()

        if choice == "1":
            bible_scraper_menu()
        elif choice == "2":
            concordance_menu()
        elif choice == "0":
            break
        else:
            print("Invalid choice.")

def bible_scraper_menu():
    while True:
        print("\n== Bible Scraper Menu ==")
        print("1. Scrape a Single Book")
        print("2. Scrape Old Testament")
        print("3. Scrape New Testament")
        print("4. Scrape Whole Bible")
        print("5. Convert Single Book to JSON")
        print("6. Convert All Books to JSON")
        print("")
        print("0. Back")
        choice = input("Select an option: ").strip()

        if choice == "1":
            book_name = input("Enter the book name: ").strip()
            if book_name in scraper.BOOK_CHAPTERS:
                scraper.scrape_single_book(book_name)
            else:
                print("Invalid book name.")
        elif choice in ["2", "3", "4"]:
            confirm = input("Are you sure you want to proceed? (Y/N): ").strip().lower()
            if confirm == "y":
                books = scraper.OLD_TESTAMENT_BOOKS if choice == "2" else \
                        scraper.NEW_TESTAMENT_BOOKS if choice == "3" else \
                        scraper.BOOK_CHAPTERS
                for book in books:
                    scraper.scrape_single_book(book)

        elif choice == "5":
            book = input("Enter book name: ").strip()
            scraper.convert_to_json(book)
        elif choice == "6":
            scraper.batch_convert_to_json()
        elif choice == "0":
            break
        else:
            print("Invalid choice.")

def concordance_menu():
    from concordance_tools import strongs_batch_scraper as sbs
    from concordance_tools.strongs_scraper import scrape_strongs_entry

    while True:
        print("\n== Concordance Scraper Menu ==")
        print("1. Scrape a Single Strong's Number (Manual Input)")
        print("2. Scrape Concordance for Old Testament (Strong's H-numbers)")
        print("3. Scrape Concordance for New Testament (Strong's G-numbers)")
        print("4. Scrape Concordance for Whole Bible (H + G)")
        print("0. Back to Main Menu")
        choice = input("Select an option: ").strip()

        if choice == "1":
            strongs_id = input("Enter Strong’s Number (e.g., H914): ").strip()
            result = scrape_strongs_entry(strongs_id)
            if result:
                print(f"✔ Success: {strongs_id}")
            else:
                print(f"❌ Failed to scrape {strongs_id}")
        elif choice == "2":
            sbs.MODE = "H"
            sbs.scrape_batch()
        elif choice == "3":
            sbs.MODE = "G"
            sbs.scrape_batch()
        elif choice == "4":
            sbs.MODE = "ALL"
            sbs.scrape_batch()
        elif choice == "0":
            break
        else:
            print("Invalid choice.")

def database_insertion_menu():
    while True:
        print("\n== Database Insertion Menu ==")
        print("1. Insert JSON for One Book")
        print("2. Insert All Books (JSON → DB)")
        print("3. Insert Complete Canon")
        print("4. Insert Cross References")
        print("0. Back")
        choice = input("Select an option: ").strip()

        if choice == "1":
            book = input("Enter book name: ").strip()
            scraper.insert_json_to_db(book)
        elif choice == "2":
            scraper.batch_insert_all_books()
        elif choice == "3":
            scraper.batch_insert_complete_canon("GoodBook.db")
        elif choice == "4":
            scraper.insert_cross_references("GoodBook.db")
        elif choice == "0":
            break
        else:
            print("Invalid choice.")

def ai_development_menu():
    from ai_tools.bible_nlp import BibleNLP
    while True:
        print("\n== AI Development Menu ==")
        print("1. Run NER on Single Book")  # For NER processing
        print("2. Run NER on All Books")
        print("3. Log Untagged Words per Verse")  # For entity validation
        print("4. NER Entity Validator Menu")
        print("5. Validator Menu:")
        print("0. Back")
        choice = input("Select an option: ").strip()

        if choice == "1":
            book_name = input("Enter book name to run full-book NER: ").strip()
            BibleNLP.run_ner_full_book(book_name, CONFIG.get("db_path", "GoodBook.db"))
        elif choice == "2":
            confirm = input("Are you sure you want to run NER on all books? (Y/N): ").strip().lower()
            if confirm == "y":
                BibleNLP.run_ner_all_books(CONFIG.get("db_path", "GoodBook.db"))
        elif choice == "3":

            book_name = input("Enter book name to analyze untagged words: ").strip()
            entity_dir = CONFIG.get("entity_dir", "bible_entities")
            db_path = CONFIG.get("db_path", "GoodBook.db")

            print(f"📂 Loading all entity files from: {entity_dir}")

            # Merge all entities from JSON files
            merged_entities = {}
            for filename in os.listdir(entity_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(entity_dir, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            for tag, entries in data.items():
                                if tag not in merged_entities:
                                    merged_entities[tag] = {}
                                merged_entities[tag].update(entries)
                        print(f"✔ Loaded {filename}")
                    except Exception as e:
                        print(f"❌ Failed to load {filename}: {e}")

            validator = EntityValidator(db_path=db_path, merged_entity_dict=merged_entities)
            validator.log_untagged_words_per_verse(book_name)
        elif choice == "4": 
            ner_entity_validator_menu()            
        elif choice == "5":
            validator_menu()
        elif choice == "0":
            break
        else:
            print("Invalid choice.")

def ner_entity_validator_menu():
    from entity_validator import EntityValidator
    import os
    import json
    import sqlite3
    """Menu for NER Entity Validator."""
    print("\n== NER Entity Validator Menu ==")
    print("This tool helps validate and alphabetize NER entity files.")
    print("It can also check entities against the Bible text for missing entries.") 

    entity_dir = CONFIG.get("entity_dir", "bible_entities")
    db_path = CONFIG.get("db_path", "GoodBook.db")

    def prompt_entity_file():
        print("\nAvailable entity files:")
        files = [f for f in os.listdir(entity_dir) if f.endswith(".json")]
        for i, f in enumerate(files, 1):
            print(f"{i}. {f}")
        print("A. All files")
        print("0. Cancel")
        choice = input("Select file (or 'A' for all): ").strip()
        if choice.lower() == "a":
            return "ALL"
        elif choice == "0":
            return None
        elif choice.isdigit() and 1 <= int(choice) <= len(files):
            return files[int(choice) - 1]
        else:
            print("Invalid choice.")
            return None

    def alphabetize_file(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for tag in data:
                if isinstance(data[tag], dict):
                    data[tag] = dict(sorted(data[tag].items(), key=lambda x: x[0]))

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"✔ Alphabetized {os.path.basename(file_path)}")

        except Exception as e:
            print(f"❌ Failed to process {file_path}: {e}")

    def alphabetize_entities():
        selection = prompt_entity_file()
        if not selection:
            return

        print("\n⚠️ WARNING: This will overwrite your entity file(s). Make a backup first!")
        confirm = input("Continue? (Y/N): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        if selection == "ALL":
            for filename in os.listdir(entity_dir):
                if filename.endswith(".json"):
                    alphabetize_file(os.path.join(entity_dir, filename))
        else:
            alphabetize_file(os.path.join(entity_dir, selection))

    def validate_entities():
        selection = prompt_entity_file()
        if not selection:
            return

        validator = EntityValidator(db_path=db_path, entity_dir=entity_dir)
        failed_matches = {}

        def validate_file(path, filename):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            missing = {}
            for tag, entries in data.items():
                for phrase in list(entries.keys()):
                    cursor.execute("SELECT COUNT(*) FROM complete_canon WHERE text LIKE ? COLLATE BINARY", (f"%{phrase}%",))
                    count = cursor.fetchone()[0]
                    if count == 0:
                        missing.setdefault(tag, []).append(phrase)
            conn.close()
            if missing:
                failed_matches[filename] = missing

        if selection == "ALL":
            for filename in os.listdir(entity_dir):
                if filename.endswith(".json"):
                    validate_file(os.path.join(entity_dir, filename), filename)
        else:
            validate_file(os.path.join(entity_dir, selection), selection)

        if not failed_matches:
            print("✅ All entities matched!")
            return

        os.makedirs("output/LOGS", exist_ok=True)
        out_path = os.path.join("output/LOGS", "missing_entities.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(failed_matches, f, indent=2)
        print(f"📄 Missing entries saved to {out_path}")

        delete = input("\nDelete unmatched entries from original file(s)? (Y/N): ").strip().lower()
        if delete != "y":
            return

        for filename, tags in failed_matches.items():
            path = os.path.join(entity_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for tag, phrases in tags.items():
                for p in phrases:
                    if p in data.get(tag, {}):
                        del data[tag][p]
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"🧹 Removed {sum(len(v) for v in tags.values())} entries from {filename}")

    while True:
        print("\n== NER Entity Validator Menu ==")
        print("1. Alphabetize Entity Files")
        print("2. Validate Entities Against Bible Text")
        print("0. Return to AI Menu")
        choice = input("Select an option: ").strip()

        if choice == "1":
            alphabetize_entities()
        elif choice == "2":
            validate_entities()
        elif choice == "0":
            break
        else:
            print("Invalid choice.")

def debug_menu():
    """Debug menu to modify settings."""
    global DEBUG_MODE, OUTPUT_DIR, CLEANUP_MODE
    while True:
        print("\nDebug Mode:")
        print(f"1. Toggle Debug Logging (Currently {'ON' if DEBUG_MODE else 'OFF'})")
        print(f"2. Change Output Directory (Currently {OUTPUT_DIR})")
        print(f"3. Toggle Cleanup Mode (Currently {'ON' if CLEANUP_MODE else 'OFF'})")
        print("4. View Current Settings")
        print("5. Test new functions here:")  # Placeholder for testing new functions
        print("0. Return to Main Menu")
        choice = input("Select an option: ")

        if choice == "1":
            DEBUG_MODE = not DEBUG_MODE
            print(f"Debug Logging is now {'ON' if DEBUG_MODE else 'OFF'}")
        elif choice == "2":
            new_dir = input("Enter new output directory: ").strip()
            if new_dir:
                OUTPUT_DIR = new_dir
                print(f"Output directory changed to {OUTPUT_DIR}")
        elif choice == "3":
            CLEANUP_MODE = not CLEANUP_MODE
            print(f"Cleanup Mode is now {'ON' if CLEANUP_MODE else 'OFF'}")
        elif choice == "4":
            print("\nCurrent Settings:")
            print(f"Debug Mode: {'ON' if DEBUG_MODE else 'OFF'}")
            print(f"Output Directory: {OUTPUT_DIR}")
            print(f"Cleanup Mode: {'ON' if CLEANUP_MODE else 'OFF'}")
            print(f"Bible Version: {BIBLE_VERSION}")
        elif choice == "5":
            book_name = input("Enter book name to update subtitles from HTML: ").strip()
            scraper.merge_html_subtitles_into_json(book_name)
        elif choice == "0":
            break
        else:
            print("Invalid selection. Try again.")

def ai_debug_menu():
    while True:
        print("\n== AI & Debug Tools Menu ==")
        print("1. Resolve Verse ID → Book/Chapter/Verse")
        print("2. Get Direct Cross-References for Verse ID")
        print("3. Get Forward Cross-References (Range)")
        print("4. Get Reverse Cross-References (Range)")
        print("9. Debug Menu (for advanced debugging)")
        print("0. Back")
        choice = input("Select an option: ").strip()

        if choice == "1":
            verse_id = input("Enter verse ID: ").strip()
            if verse_id.isdigit():
                print(scraper.resolve_verse_id(int(verse_id)))
            else:
                print("Invalid input. Please enter a number.")

        elif choice == "2":
            verse_id = input("Enter verse ID: ").strip()
            if verse_id.isdigit():
                refs = scraper.get_cross_references_for_verse_id(int(verse_id))
                for ref in refs:
                    print(ref)
            else:
                print("Invalid input. Please enter a number.")

        elif choice == "3":
            rng = input("Enter verse ID or range (e.g. 100-105): ").strip()
            refs = scraper.get_cross_references(rng, direction="forward")
            for ref in refs:
                print(ref)

        elif choice == "4":
            rng = input("Enter verse ID or range (e.g. 100-105): ").strip()
            refs = scraper.get_cross_references(rng, direction="reverse")
            for ref in refs:
                print(ref)
        elif choice == "9":
            debug_menu()
        elif choice == "0":
            break
        else:
            print("Invalid choice.")

def validator_menu():
    while True:
        print("1. Validator: Check for Substring Conflicts")
        print("2. Validator: Check for Entity Conflicts")
        print("3. Validator: Check for Entity Overlaps")
        print("4. Validator: Check for Entity Overlaps (with Bible Text)")
        choice = input("Select an option: ").strip()

        if choice == "1":
            run_entity_validation()
        elif choice == "2":
            print("For future use...")
        elif choice == "3":
            print("For future use...")
        elif choice == "4":
            print("For future use...")
        elif choice == "0":
            break
        else:
            print ("Invalid choice: ")

def run_entity_validation():
    from entity_validator import EntityValidator

    entity_file = os.path.join(CONFIG.get("entity_dir", "entities"), "measurements.json")
    db_path = CONFIG.get("db_path", "GoodBook.db")

    validator = EntityValidator(entity_file=entity_file, db_path=db_path)
    validator.load_entities()
    validator.load_bible_text_from_db("Genesis", chapter_range=(1, 1))
    validator.scan_for_substring_conflicts()
    validator.print_conflict_report()

if __name__ == "__main__":
    main_menu()