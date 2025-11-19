# This code is part of the Bible Study Game project.
# It is licensed under the GNU General Public License v3.0.
# This script parses the HTML content of a Bible passage page from BibleGateway's PRINT interface.
# It extracts the book name and chapter number from the header.

from bs4 import BeautifulSoup

class PrintPageParser:
    def __init__(self, html_file_path):
        self.html_file_path = html_file_path
        self.soup = None

    def load_html(self):
        with open(self.html_file_path, "r", encoding="utf-8") as f:
            self.soup = BeautifulSoup(f, "html.parser")
        print("✅ HTML loaded successfully.")

    def parse_book_and_chapter(self):
        if not self.soup:
            raise ValueError("HTML not loaded. Call load_html() first.")

        # Find the <h1> inside the main passage div
        passage_div = self.soup.find("div", class_="passage")
        if not passage_div:
            raise ValueError("Cannot find main passage div!")

        header = passage_div.find("h1")
        if not header:
            raise ValueError("Cannot find header <h1> inside passage!")

        full_title = header.get_text(strip=True)  # e.g., "Genesis 1"
        print(f"📖 Found Header Text: {full_title}")

        # Split into Book and Chapter
        parts = full_title.split()
        if len(parts) < 2:
            raise ValueError(f"Unexpected format in header: {full_title}")

        book = " ".join(parts[:-1])  # All except the last part
        chapter = parts[-1]

        try:
            chapter = int(chapter)
        except ValueError:
            raise ValueError(f"Chapter part '{chapter}' is not a number!")

        return book, chapter