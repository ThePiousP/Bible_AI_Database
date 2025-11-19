import requests
from bs4 import BeautifulSoup
import logging
import os
import re  # Importing regex

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)  # Ensure the output folder exists

# Setup logging
LOG_FILE = os.path.join(OUTPUT_DIR, "webverify.log")
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Dictionary of books and chapter counts (Old + New Testaments merged)
OLD_TESTAMENT_BOOKS = {
    "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34,
    "Joshua": 24, "Judges": 21, "Ruth": 4, "1 Samuel": 31, "2 Samuel": 24,
    "1 Kings": 22, "2 Kings": 25, "1 Chronicles": 29, "2 Chronicles": 36, "Ezra": 10,
    "Nehemiah": 13, "Esther": 10, "Job": 42, "Psalms": 150, "Proverbs": 31,
    "Ecclesiastes": 12, "Song of Solomon": 8, "Isaiah": 66, "Jeremiah": 52,
    "Lamentations": 5, "Ezekiel": 48, "Daniel": 12, "Hosea": 14, "Joel": 3,
    "Amos": 9, "Obadiah": 1, "Jonah": 4, "Micah": 7, "Nahum": 3, "Habakkuk": 3,
    "Zephaniah": 3, "Haggai": 2, "Zechariah": 14, "Malachi": 4
}

NEW_TESTAMENT_BOOKS = {
    "Matthew": 28, "Mark": 16, "Luke": 24, "John": 21, "Acts": 28,
    "Romans": 16, "1 Corinthians": 16, "2 Corinthians": 13, "Galatians": 6,
    "Ephesians": 6, "Philippians": 4, "Colossians": 4, "1 Thessalonians": 5,
    "2 Thessalonians": 3, "1 Timothy": 6, "2 Timothy": 4, "Titus": 3,
    "Philemon": 1, "Hebrews": 13, "James": 5, "1 Peter": 5, "2 Peter": 3,
    "1 John": 5, "2 John": 1, "3 John": 1, "Jude": 1, "Revelation": 22
}

BOOK_CHAPTERS = {**OLD_TESTAMENT_BOOKS, **NEW_TESTAMENT_BOOKS}

def get_valid_book_name():
    while True:
        book_name = input("Enter the book name: ").strip()
        if book_name in BOOK_CHAPTERS:
            logging.info(f"User entered book: {book_name}")
            return book_name
        else:
            print("Invalid book name. Please enter a valid book.")

def get_valid_chapter_number(book_name):
    max_chapters = BOOK_CHAPTERS[book_name]
    while True:
        try:
            chapter_number = int(input(f"Enter chapter number (1-{max_chapters}): "))
            if 1 <= chapter_number <= max_chapters:
                return chapter_number
            else:
                print(f"Invalid chapter. Please enter a number between 1 and {max_chapters}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def fetch_chapter_data(book_name, chapter_number):
    url = f"https://www.biblegateway.com/passage/?search={book_name}+{chapter_number}&version=NKJV"
    response = requests.get(url)

    if response.status_code != 200:
        logging.error(f"Failed to retrieve page for {book_name} {chapter_number}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    passage_section = soup.find('div', class_='passage-content')
    
    if passage_section:
        passage_text = passage_section.get_text(separator="\n").strip()
        return passage_text
    else:
        logging.info(f"No verses found for {book_name} {chapter_number}")
        return None

def fetch_and_save_chapters(book_name):
    filename = os.path.join(OUTPUT_DIR, f"{book_name}_raw.txt")
    
    with open(filename, "w", encoding="utf-8") as file:
        file.write(f"Book: {book_name}\n\n")

    for chapter_number in range(1, BOOK_CHAPTERS[book_name] + 1):
        passage_text = fetch_chapter_data(book_name, chapter_number)
        if passage_text:
            with open(filename, "a", encoding="utf-8") as file:
                file.write(f"[{book_name} {chapter_number}]\n{passage_text}\n\n")
            logging.info(f"Saved Chapter {chapter_number} of {book_name}")

def book_menu():
    book_name = get_valid_book_name()
    fetch_and_save_chapters(book_name)
    while True:
        print("\nBook Menu:")
        print("1. Print the entire book")
        print("2. Print a specific chapter")
        print("3. Return to main menu")
        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            fetch_and_display(book_name)
        elif choice == "2":
            chapter_number = get_valid_chapter_number(book_name)
            fetch_and_display(book_name, chapter_number)
        elif choice == "3":
            break
        else:
            print("Invalid choice, please try again.")

def fetch_and_display(book_name, chapter_number=None):
    filename = os.path.join(OUTPUT_DIR, f"{book_name}_raw.txt")
    
    if not os.path.exists(filename):
        print(f"Error: No data found for {book_name}. Please fetch the data first.")
        return

    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()
    
    if chapter_number:
        chapter_heading = f"[{book_name} {chapter_number}]"
        displaying = False
        for line in lines:
            if line.strip() == chapter_heading:
                displaying = True
            elif displaying and line.strip().startswith("["):
                break
            if displaying:
                print(line, end="")
    else:
        print("".join(lines))


def clean_raw_file(book_name):
    """Cleans the raw output file by:
    - Removing references in brackets and parentheses.
    - Removing 'Footnotes' and everything after it only on the line immediately after '[Book Chapter]'.
    - Formatting Cross References and Footnotes properly without extra blank lines.
    - Removing any leading commas and trimming whitespace from all lines.
    - Running the final cleanup pass twice to ensure thorough removal.
    """
    
    raw_file = os.path.join(OUTPUT_DIR, f"{book_name}_raw.txt")
    cleaned_file = os.path.join(OUTPUT_DIR, f"{book_name}_cleaned.txt")

    if not os.path.exists(raw_file):
        print(f"Error: {raw_file} not found!")
        logging.error(f"Error: {raw_file} not found!")
        return

    with open(raw_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    cleaned_lines = []
    skip_next = False  # Flag to track when to check for "Footnotes"
    in_cross_references = False
    in_footnotes = False

    for i, line in enumerate(lines):
        # If previous line was a chapter header, check the next line for "Footnotes"
        if skip_next:
            if "Footnotes" in line:
                line = re.sub(r"Footnotes.*", "", line).strip()  # Remove everything after "Footnotes"
                if line == "":  # If the line is now empty, don't add it
                    continue
            
        # Check if this is a chapter header in the format: [Book Chapter]
        if re.match(rf"\[{book_name} \d+\]", line.strip()):
            skip_next = True  # Mark the next line for checking
        else:
            skip_next = False  # Reset flag if it's not a chapter header

        # Normalize spacing between Cross References and Footnotes
        if "Cross References:" in line:
            in_cross_references = True
            cleaned_lines.append("\nCross References:\n")  # Ensure a single newline before
            continue  # Skip duplicate headers
        
        if "Footnotes:" in line:
            in_cross_references = False  # Turn off Cross References mode
            in_footnotes = True
            cleaned_lines.append("\nFootnotes:\n")  # Ensure a single newline before
            continue  # Skip duplicate headers
        
        # If within Cross References or Footnotes, ensure there are no extra blank lines
        if in_cross_references or in_footnotes:
            if line.strip() == "":  # Skip blank lines inside these sections
                continue
        
        # Remove bracketed and parenthesized references (also handles digits)
        line = re.sub(r"\s?[\[\(]\s?[a-zA-Z0-9]{1,3}\s?[\]\)]\s?", " ", line)

        # **Final Cleanup:**
        # - Remove leading commas
        # - Trim leading/trailing whitespace
        line = re.sub(r"^\s*,\s", "", line).strip()

        cleaned_lines.append(line + "\n")  # Ensure each line ends with a newline

    # **Run the final cleanup process TWICE for thoroughness**
    for _ in range(2):
        cleaned_lines = [re.sub(r"^\s*,\s*", "", line).strip() + "\n" for line in cleaned_lines]

    # Save cleaned content
    with open(cleaned_file, "w", encoding="utf-8") as file:
        file.writelines(cleaned_lines)

    print(f"Cleaned file saved as: {cleaned_file}")
    logging.info(f"Cleaned file saved as: {cleaned_file}")

def main_menu():
    while True:
        print("\nMain Menu:")
        print("1. Process a Book")
        print("2. Process Old Testament")
        print("3. Process New Testament")
        print("4. Process Whole Bible")
        print("5. Exit")
        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            book_menu()
        elif choice == "2":
            for book in OLD_TESTAMENT_BOOKS.keys():
                fetch_and_display(book)
        elif choice == "3":
            for book in NEW_TESTAMENT_BOOKS.keys():
                fetch_and_display(book)
        elif choice == "4":
            for book in BOOK_CHAPTERS.keys():
                fetch_and_display(book)
        elif choice == "5":
            exit(0)
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main_menu()
