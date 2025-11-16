# concordance_tools/strongs_scraper.py
import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

OUTPUT_DIR = "output/concordance"
LOG_DIR = "output/logs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

def clean_text(text):
    text = text.replace("(Key)", " ").replace("Listen", " ")
    text = re.sub(r"(?<=[a-zA-Z])(?=[A-Z][a-z])", " ", text)  # Insert space before capital words
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)          # Fix camelCase or joinedwords
    text = re.sub(r"(?<=[a-zA-Z])(?=[0-9])", " ", text)      # Space between word and number
    text = re.sub(r"(?<=[,:])(?=[^\s])", ": ", text)       # Add space after colons and commas
    text = re.sub(r"\s{2,}", " ", text)                     # Collapse multiple spaces
    return text.strip()

def clean_definition(text):
    text = re.sub(r"::", ":", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

def extract_kjv_translation(text):
    match = re.search(r"The KJV translates Strong's [^:]+: (.+)", text)
    return clean_text(match.group(1)) if match else clean_text(text)

def split_outline_text(text):
    segments = re.split(r"(?<=[.])\s+|(?<=[a-z])(?=[A-Z])|(?<=[a-z])(?=[a-z][A-Z])", text)
    return [clean_text(seg) for seg in segments if seg.strip()]

def scrape_strongs_entry(strongs_number):
    url = f"https://www.blueletterbible.org/lexicon/{strongs_number.lower()}/nkjv/"
    response = requests.get(url)

    log = {
        "timestamp": datetime.now().isoformat(),
        "strongs_number": strongs_number,
        "url": url,
        "status": response.status_code,
        "error": None
    }

    if response.status_code != 200:
        log["error"] = f"HTTP {response.status_code}"
        save_log(log)
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    data = {
        "strongs_number": strongs_number,
        "lemma": "",
        "transliteration": "",
        "pronunciation": "",
        "pos": "",
        "etymology": "",
        "kjv_translation_count": "",
        "outline": [],
        "definition": "",
        "has_outline": False
    }

    try:
        lemma_tag = soup.select_one(".lexical strong") or soup.select_one("h6")
        if lemma_tag:
            data["lemma"] = clean_text(lemma_tag.get_text(" ", strip=True))

        def extract_field(label):
            tag = soup.find("div", string=label)
            if tag:
                next_div = tag.find_next("div")
                return clean_text(next_div.get_text(" ", strip=True)) if next_div else ""
            return ""

        data["transliteration"] = extract_field("Transliteration")
        data["pronunciation"] = extract_field("Pronunciation")
        data["pos"] = extract_field("Part of Speech")
        data["etymology"] = extract_field("Root Word (Etymology")

        kjv_heading = soup.find(string=lambda x: x and "KJV Translation Count" in x)
        if kjv_heading:
            next_block = kjv_heading.find_next("div")
            if next_block:
                raw = next_block.get_text(" ", strip=True)
                data["kjv_translation_count"] = extract_kjv_translation(raw)

        outline_heading = soup.find(string=lambda x: x and "Outline of Biblical Usage" in x)
        if outline_heading:
            possible_lists = outline_heading.find_all_next(["ul", "ol", "div", "p"], limit=3)
            for element in possible_lists:
                li_items = element.find_all("li")
                if li_items:
                    blocked_keywords = ["daily", "grace", "checkbook", "bible reading", "morning", "evening"]
                    filtered = [clean_text(li.get_text(" ", strip=True)) for li in li_items if not any(x in li.get_text(strip=True).lower() for x in blocked_keywords)]
                    if filtered:
                        data["outline"] = filtered
                        data["has_outline"] = True
                        break
                else:
                    fallback_text = element.get_text(" ", strip=True)
                    split_items = split_outline_text(fallback_text)
                    if split_items:
                        data["outline"] = split_items
                        data["has_outline"] = True
                        break

        def_heading = soup.find(string=lambda x: x and "Strong’s Definitions" in x)
        if def_heading:
            def_para = def_heading.find_next("p")
            if def_para:
                text = def_para.get_text(" ", strip=True)
                data["definition"] = clean_definition(text)

        save_json(data)
        log["status"] = "OK"
        print(f"✔ Scraped {strongs_number}")
    except Exception as e:
        log["error"] = f"{type(e).__name__}: {str(e)}"
        print(f"❌ Failed to parse {strongs_number}: {e}")

    save_log(log)
    return data

def save_json(data):
    strongs_id = data.get("strongs_number", "unknown")
    out_path = os.path.join(OUTPUT_DIR, f"{strongs_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_log(log_data):
    log_path = os.path.join(LOG_DIR, "strongs_scraper_log.json")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(log_data)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
