from playwright.sync_api import sync_playwright

def scrape_passage(book="Genesis", chapter=1):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="biblegateway_session.json")
        page = context.new_page()

        url = f"https://www.biblegateway.com/passage/?search={book}+{chapter}&version=NKJV"
        print(f"🌐 Navigating to {url}")
        page.goto(url)
        page.wait_for_timeout(8000)  # Wait for full load (including study notes)

        html = page.content()

        filename = f"{book}_{chapter}_plus.html".replace(" ", "_")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✅ Page HTML saved to {filename}")
        browser.close()

if __name__ == "__main__":
    scrape_passage("Genesis", 1)