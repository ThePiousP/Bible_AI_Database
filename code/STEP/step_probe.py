# step_probe.py
# Read-only DOM scout for STEP Bible running at http://localhost:8989/
# - Picks a robust verse selector
# - Prints the first verse's outerHTML
# - Lists Strong's attributes it finds
# - Saves full page HTML to cache/html (from config.json)

import json, os, sys, time
from pathlib import Path

URL = "http://localhost:8989/?q=version=KJV@reference=Gen.22&options=NHVUG"

# Candidate selectors to try (ordered, most-specific first)
VERSE_CANDIDATES = [
    "div.verse",
    "span.verse",
    "[data-verse-id]",
    "[data-osis]",
    'div[class*="verse"]',
]

VERSE_NUMBER_SUB = [
    ".verseNumber",
    ".vnum",
    ".v-num",
    ".verse-num",
    "[data-verse]",
]

# Strong’s hooks (we’ll test in this order)
STRONG_TOKEN_CANDS = [
    "[data-strong]",
    "a[data-lemma]",
    "span[data-lemma]",
    'a[class*="lemma"]',
    'span[class*="lemma"]',
]

FOOTNOTE_CANDS = [
    "a.footnote",
    'a[rel="footnote"]',
    "sup.note",
    "sup.footnote",
    "[data-footnote]",
    "[data-note]",
]

def load_config():
    # Try to find config.json near cwd first
    search = [
        Path.cwd() / "config.json",
        Path(__file__).resolve().parent / "config.json",
    ]
    for p in search:
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
    # Fallback defaults if not found
    return {"html_cache_dir": "cache/html", "logging_dir": "output/LOGS"}

def ensure_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def pick_best_selector(page):
    """
    Heuristic: choose the selector that yields the most nodes AND
    at least 80% of its nodes appear to start with a verse number.
    """
    best = None
    best_count = 0
    best_ratio = 0.0

    for sel in VERSE_CANDIDATES:
        try:
            elements = page.query_selector_all(sel)
            count = len(elements)
            if count == 0:
                continue

            # crude "looks like a verse" check: leading integer somewhere in first 10 chars
            looks_like = 0
            for el in elements:
                txt = (el.inner_text() or "").strip()
                head = txt[:10]
                if any(ch.isdigit() for ch in head):
                    looks_like += 1
            ratio = looks_like / max(count, 1)

            # prefer more nodes; break ties by higher ratio
            if count > best_count or (count == best_count and ratio > best_ratio):
                best = sel
                best_count = count
                best_ratio = ratio
        except Exception:
            pass

    return best, best_count, best_ratio

def first_hit(page, sel_list, scope=None):
    base = scope if scope is not None else page
    for s in sel_list:
        el = base.query_selector(s)
        if el:
            return s, el
    return None, None

def main():
    cfg = load_config()
    cache_dir = Path(cfg.get("html_cache_dir") or cfg.get("cache_dir") or "cache/html")
    out_html = cache_dir / "STEP_Gen22.html"
    ensure_dir(out_html)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright not installed. Run:\n  pip install playwright\n  playwright install chromium")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"🌐 Navigating to: {URL}")
        page.goto(URL, wait_until="domcontentloaded", timeout=60_000)

        # Let client-side scripts finish rendering (STEP is SPA-like)
        page.wait_for_timeout(1500)

        sel, count, ratio = pick_best_selector(page)
        if not sel:
            print("❌ Could not find any verse containers with the given candidates.")
            print("   Try changing the chapter in URL or open with headless=False and inspect.")
            browser.close()
            return

        print(f"✅ Verse selector: {sel}  (count={count}, ratio~{ratio:.2f})")
        verses = page.query_selector_all(sel)
        first = verses[0] if verses else None
        if not first:
            print("❌ No verse nodes found after selector pick.")
            browser.close()
            return

        # Verse number
        vnum_sel, vnum_el = first_hit(page=None, sel_list=VERSE_NUMBER_SUB, scope=first)
        vnum_text = (vnum_el.inner_text().strip() if vnum_el else None)
        if vnum_text:
            print(f"🔹 Verse number via {vnum_sel}: {vnum_text}")
        else:
            print("🔹 Verse number: (not found via common sub-selectors)")

        # Strong’s tokens inside the first verse
        strong_hits = []
        for cand in STRONG_TOKEN_CANDS:
            for el in first.query_selector_all(cand):
                strong = el.get_attribute("data-strong") or el.get_attribute("data-lemma")
                t = (el.inner_text() or "").strip()
                if strong or t:
                    strong_hits.append((cand, t, strong))
        if strong_hits:
            print(f"🔹 Found {len(strong_hits)} Strong’s-bearing tokens (first 6 shown):")
            for cand, t, s in strong_hits[:6]:
                print(f"   - [{cand}] text='{t}' strong='{s}'")
        else:
            print("🔹 No Strong’s-bearing tokens found in the first verse (check other verses/selectors).")

        # Footnotes in the first verse
        foots = []
        for cand in FOOTNOTE_CANDS:
            for el in first.query_selector_all(cand):
                marker = (el.inner_text() or "").strip()
                href = el.get_attribute("href") or el.get_attribute("data-note") or el.get_attribute("data-footnote")
                if marker or href:
                    foots.append((cand, marker, href))
        if foots:
            print(f"🔹 Found {len(foots)} footnote markers (first 4 shown):")
            for cand, m, h in foots[:4]:
                print(f"   - [{cand}] marker='{m}' ref='{h}'")
        else:
            print("🔹 No footnotes detected in the first verse.")

        # Print the first verse outerHTML for manual selector confirmation
        html_snippet = page.evaluate("(el) => el.outerHTML", first)
        print("\n===== FIRST VERSE outerHTML =====")
        print(html_snippet[:2000] + ("...[snip]..." if len(html_snippet) > 2000 else ""))
        print("=================================\n")

        # Save the whole page HTML
        full_html = page.content()
        out_html.write_text(full_html, encoding="utf-8")
        print(f"💾 Saved full page HTML → {out_html.resolve()}")

        browser.close()

if __name__ == "__main__":
    main()
