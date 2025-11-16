# export_genesis1_jsonl.py
# Creates: C:\BIBLE\data\genesis1.jsonl  (one verse per line, with meta)

import os, sqlite3, json

DB_PATH = r"C:\BIBLE\concordance.db"   # <-- change if your DB is elsewhere
OUT_DIR = r"C:\BIBLE\data"
OUT_FILE = os.path.join(OUT_DIR, "genesis1.jsonl")

os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# verses.text_plain + books/chapters join (matches your schema)
sql = """
SELECT
  v.id            AS verse_id,
  b.book_name     AS book,
  c.chapter_number AS chapter,
  v.verse_num     AS verse,
  v.text_plain    AS text
FROM verses v
JOIN chapters c ON v.chapter_id = c.id
JOIN books b    ON v.book_id = b.id
WHERE b.book_name = 'Genesis' AND c.chapter_number = 1
ORDER BY v.verse_num
"""
rows = cur.execute(sql).fetchall()
conn.close()

with open(OUT_FILE, "w", encoding="utf-8") as f:
    for r in rows:
        ref = f"{r['book']} {r['chapter']}:{r['verse']}"
        obj = {
            "text": r["text"] if r["text"] else "",
            "meta": {
                "ref": ref,
                "verse_id": int(r["verse_id"]),
                "book": r["book"],
                "chapter": int(r["chapter"]),
                "verse": int(r["verse"]),
            }
        }
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

print(f"Wrote {len(rows)} lines to {OUT_FILE}")
