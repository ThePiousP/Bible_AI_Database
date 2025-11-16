from playwright.sync_api import sync_playwright

def manual_login_and_save():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Go to the home page or login page
        page.goto("https://www.biblegateway.com/")

        print("🔓 Log in to BibleGateway Plus in this browser window.")
        print("✅ Once you're logged in and you see your name/account, close the window.")

        # Wait for manual login and session confirmation
        page.wait_for_timeout(120_000)  # 2 minutes
        context.storage_state(path="biblegateway_session.json")
        browser.close()

if __name__ == "__main__":
    manual_login_and_save()