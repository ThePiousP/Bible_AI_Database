# This script processes biblical text for Named Entity Recognition (NER) using spaCy.
# It extracts entities such as people, places, and organizations from the text.
# @staticmethod is used to add a utility function that doesn't need access to or the ability to
# modify the state of the class or its instances. 

import os
import sys
import re
import json
import sqlite3
from entity_validator import EntityValidator
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Iterable, Any, Set

# Optional: spaCy is only needed if you want ruler-based gazetteers and/or to export to spaCy formats
try:
    import spacy
    from spacy.language import Language
    from spacy.pipeline import EntityRuler
except Exception:
    spacy = None
    Language = None
    EntityRuler = None

@dataclass
class VerseRow:
    id: int
    book: str
    chapter: int
    verse_num: int
    text_plain: str

@dataclass
class TokenRow:
    id: int
    verse_id: int
    token_idx: int
    text: str
    strong_norm: Optional[str]  # e.g., "H0430"
    morph_norm: Optional[str]
    italics: bool


# ✅ Load config directly from JSON
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


class BibleNLP:
    @staticmethod
    def run_ner_full_book(book_name, db_path):
        validator = EntityValidator(config_path="config.json", entity_dir="bible_entities", db_path=db_path)
        validator.load_config()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get total chapters in this book
        query = """
            SELECT MAX(c.chapter_number)
            FROM chapters c
            JOIN books b ON c.book_id = b.id
            WHERE b.book_name = ?
        """
        cursor.execute(query, (book_name,))
        result = cursor.fetchone()
        if not result or not result[0]:
            conn.close()
            return

        total_chapters = result[0]

        # One-time spaCy init per book (keeps things fast & deterministic)
        if validator.nlp is None:
            try:
                import spacy
                validator.nlp = spacy.load("en_core_web_lg")
            except Exception:
                # Fall back to a lightweight blank model if lg isn't available
                import spacy
                validator.nlp = spacy.blank("en")
            validator.inject_entity_ruler()  # load patterns into the pipeline once
            # Load multi-label metadata once per book (safe if file missing)
            try:
                ml_lookup = load_multilabel_lookup(os.path.join(CONFIG.get('entity_dir','bible_entities'), 'DEITY_master_KJV.json'))
            except Exception:
                try:
                    ml_lookup = load_multilabel_lookup(os.path.join(CONFIG.get('entity_dir','bible_entities'), 'DEITY_with_multilabel_context.json'))
                except Exception:
                    ml_lookup = None

        log_dir = os.path.join("output", "ner_logs", book_name)
        os.makedirs(log_dir, exist_ok=True)

        for chapter in range(1, total_chapters + 1):
            query = """
                SELECT b.book_name, c.chapter_number, v.verse_number, v.text
                FROM verses v
                JOIN chapters c ON v.chapter_id = c.id
                JOIN books b ON c.book_id = b.id
                WHERE b.book_name = ? AND c.chapter_number = ?
                ORDER BY v.verse_number
            """
            cursor.execute(query, (book_name, chapter))
            verses = cursor.fetchall()

            log_path = os.path.join(log_dir, f"{book_name}_{chapter}.txt")
            with open(log_path, "w", encoding="utf-8") as log_file:
                header = f"\n===== {book_name} Chapter {chapter} =====\n"
                log_file.write(header)

                for book, chap, verse, text in verses:
                    verse_header = f"\n[{book} {chap}:{verse}] {text}\n"
                    log_file.write(verse_header)

                    validator.doc = validator.nlp(text)
                    # Attach alternate labels contextually (does not change ent.label_)
                    try:
                        verse_uid = f"{book}.{chap}.{verse}"
                        if 'ml_lookup' in locals() and ml_lookup:
                            apply_alt_labels(validator.doc, verse_uid, ml_lookup)
                    except Exception:
                        pass
                    ents = list(validator.doc.ents)

                    if ents:
                        log_file.write("Entities:\n")
                        for ent in ents:
                            line = f"  - {ent.text} ({ent.label_})\n"
                            log_file.write(line)
                    else:
                        log_file.write("No entities found.\n")

        # Full-book untagged words report
        full_query = """
            SELECT b.book_name, c.chapter_number, v.verse_number, v.text
            FROM verses v
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE b.book_name = ?
            ORDER BY c.chapter_number, v.verse_number
        """
        cursor.execute(full_query, (book_name,))
        all_verses = cursor.fetchall()
        validator.bible_text = " ".join(v[3] for v in all_verses if v[3])
        validator.log_untagged_words_per_verse(book_name)
        validator.save_untagged_log(book_name)

        conn.close()

        # (Optional) merge entity JSON files — if you want to use this merged dict,
        # inject it BEFORE tagging (above). If you only want the final log, you can leave it here.
        entity_dir = CONFIG.get("entity_dir", "bible_entities")
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
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")

        # If you want to re-run logs with merged entities, do a second pass here; otherwise omit.
        # validator2 = EntityValidator(db_path=db_path, merged_entity_dict=merged_entities)
        # validator2.log_untagged_words_per_verse(book_name)

    @staticmethod
    def run_ner_all_books(db_path):
        """
        Iterates all books present in the DB (ordered by books.id), running run_ner_full_book().
        No dependency on external modules.
        """
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            # Expect a 'books' table with 'id' and 'book_name'
            cur.execute("SELECT book_name FROM books ORDER BY id ASC")
            rows = cur.fetchall()
            books = [r[0] for r in rows]
        except Exception as e:
            print(f"❌ Could not enumerate books from DB: {e}")
            return
        finally:
            try:
                con.close()
            except Exception:
                pass

        if not books:
            print("No books found in DB.")
            return

        print("\n📚 Running NER on ALL books...\n")
        success_count = 0
        failure_log = []

        for book_name in books:
            print(f"📖 Processing: {book_name}")
            try:
                BibleNLP.run_ner_full_book(book_name, db_path)
                success_count += 1
            except Exception as e:
                print(f"❌ Failed: {book_name} — {e}")
                failure_log.append((book_name, str(e)))

        print(f"\n✅ Done. Success: {success_count}, Failed: {len(failure_log)}")
        if failure_log:
            print("Failures:")
            for book, error in failure_log:
                print(f"  - {book}: {error}")


    @staticmethod
    def load_strongs_entity_map(path: str) -> Dict[str, Dict[str, str]]:
        p = Path(path)
        if not p.exists():
            return {}
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        norm = {}
        for k, v in data.items():
            k2 = k.strip().upper()
            if k2.startswith(("H", "G")):
                head = k2[0]
                num = re.sub(r"\D", "", k2[1:])
                norm[f"{head}{int(num):04d}"] = v
        return norm

    @staticmethod
    def load_overrides(db_path: Optional[str] = None,
                    json_path: Optional[str] = None) -> Dict[Tuple[str,int,int], List[Tuple[int,int,str,str]]]:
        overrides: Dict[Tuple[str,int,int], List[Tuple[int,int,str,str]]] = {}
        if db_path and Path(db_path).exists():
            try:
                con = sqlite3.connect(db_path)
                cur = con.cursor()
                cur.execute("""
                    SELECT book, chapter, verse, start_char, end_char, tag, COALESCE(note,'')
                    FROM entity_overrides
                """)
                for book, ch, vn, s, e, tag, note in cur.fetchall():
                    overrides.setdefault((book, int(ch), int(vn)), []).append((int(s), int(e), str(tag), str(note)))
            except sqlite3.Error:
                pass
            finally:
                try:
                    con.close()
                except Exception:
                    pass
        if json_path and Path(json_path).exists():
            data = json.loads(Path(json_path).read_text(encoding="utf-8"))
            for ref, items in data.items():
                m = re.match(r"^\s*([1-3]?\s?[A-Za-z ]+)\s+(\d+):(\d+)\s*$", ref)
                if not m:
                    continue
                book, ch, vn = m.group(1).strip(), int(m.group(2)), int(m.group(3))
                for it in items:
                    overrides.setdefault((book, ch, vn), []).append(
                        (int(it["start"]), int(it["end"]), str(it["tag"]), str(it.get("note","")))
                    )
        return overrides

    @staticmethod
    def load_gazetteer_patterns_from_dir(dir_path: str) -> List[Dict[str, Any]]:
        patterns: List[Dict[str, Any]] = []
        dp = Path(dir_path)
        if not dp.exists():
            return patterns
        for p in sorted(dp.glob("*.json")):
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(obj, dict) and "patterns" in obj and isinstance(obj["patterns"], list):
                    patterns.extend(obj["patterns"])
                elif isinstance(obj, list):
                    patterns.extend(obj)
            except Exception:
                continue
        clean = []
        for pat in patterns:
            if not isinstance(pat, dict): 
                continue
            label = pat.get("label")
            pattern = pat.get("pattern")
            if not label or not pattern:
                continue
            clean.append({"label": str(label), "pattern": pattern})
        return clean

    @staticmethod
    def build_nlp_with_gazetteers(patterns: List[Dict[str, Any]],
                                overwrite_ents: bool = True,
                                case_sensitive: bool = True):
        if 'spacy' not in globals() or spacy is None:
            return None
        nlp = spacy.blank("xx")
        ruler = nlp.add_pipe("entity_ruler", config={"overwrite_ents": overwrite_ents})
        ruler.add_patterns(patterns)
        if case_sensitive:
            try:
                nlp.vocab.lookups.add_table("lexeme_norm", {})
            except Exception:
                pass
        return nlp

    @staticmethod
    def align_tokens_in_verse_text(verse_text: str, token_texts: List[str]) -> List[Tuple[int,int]]:
        spans: List[Tuple[int,int]] = []
        pos = 0
        for t in token_texts:
            if not t:
                spans.append((-1, -1)); continue
            i = verse_text.find(t, pos)
            if i < 0:
                i = verse_text.find(t)
            if i < 0:
                spans.append((-1, -1)); continue
            s, e = i, i + len(t)
            spans.append((s, e))
            pos = e
        return spans

    @staticmethod
    def spans_from_strongs(tokens: List["TokenRow"],
                        verse_text: str,
                        strongs_map: Dict[str, Dict[str, str]],
                        prefer_multiword_merge: bool = True) -> List[Tuple[int,int,str,Dict[str,Any]]]:
        token_texts = [t.text for t in tokens]
        char_spans = BibleNLP.align_tokens_in_verse_text(verse_text, token_texts)
        raw_spans: List[Tuple[int,int,str,Dict[str,Any]]] = []
        for tok, (s,e) in zip(tokens, char_spans):
            if s < 0 or not tok.strong_norm:
                continue
            sn = tok.strong_norm.strip().upper()
            if not re.match(r"^[HG]\d{4}$", sn):
                head = sn[0]
                num = re.sub(r"\D", "", sn[1:])
                sn = f"{head}{int(num):04d}"
            meta = strongs_map.get(sn)
            if not meta:
                continue
            tag = meta.get("tag")
            if not tag:
                continue
            canon = meta.get("canonical", "")
            raw_spans.append((s, e, tag, {"source":"strongs", "strong": sn, "canonical": canon}))
        if not prefer_multiword_merge or not raw_spans:
            return raw_spans
        raw_spans.sort(key=lambda x: (x[0], x[1]))
        merged: List[Tuple[int,int,str,Dict[str,Any]]] = []
        cs, ce, ctag, cmeta = raw_spans[0]
        for s, e, tag, meta in raw_spans[1:]:
            if tag == ctag and s == ce:
                ce = e
            else:
                merged.append((cs, ce, ctag, cmeta))
                cs, ce, ctag, cmeta = s, e, tag, meta
        merged.append((cs, ce, ctag, cmeta))
        return merged

    @staticmethod
    def spans_from_gazetteer(nlp, verse_text: str) -> List[Tuple[int,int,str,Dict[str,Any]]]:
        if nlp is None:
            return []
        doc = nlp(verse_text)
        out: List[Tuple[int,int,str,Dict[str,Any]]] = []
        for ent in doc.ents:
            out.append((int(ent.start_char), int(ent.end_char), ent.label_, {"source":"gazetteer"}))
        return out

    @staticmethod
    def merge_spans_with_priority(strongs_spans: List[Tuple[int,int,str,Dict[str,Any]]],
                                gaz_spans: List[Tuple[int,int,str,Dict[str,Any]]],
                                priority: Tuple[str, str] = ("strongs","gazetteer")) -> List[Tuple[int,int,str,Dict[str,Any]]]:
        all_spans = strongs_spans + gaz_spans
        all_spans.sort(key=lambda x: (x[0], -(x[1]-x[0])))
        final: List[Tuple[int,int,str,Dict[str,Any]]] = []
        def overlaps(a, b):
            return not (a[1] <= b[0] or b[1] <= a[0])
        for span in all_spans:
            keep = True
            for j, chosen in enumerate(final):
                if overlaps(span, chosen):
                    if span[0] == chosen[0] and span[1] == chosen[1] and span[2] == chosen[2]:
                        keep = False
                        break
                    p_src = span[3].get("source","")
                    c_src = chosen[3].get("source","")
                    if priority.index(p_src) < priority.index(c_src):
                        final[j] = span
                    keep = False
                    break
            if keep:
                final.append(span)
        final.sort(key=lambda x: (x[0], x[1]))
        return final

    @staticmethod
    def apply_overrides_to_spans(spans: List[Tuple[int,int,str,Dict[str,Any]]],
                                verse_key: Tuple[str,int,int],
                                overrides: Dict[Tuple[str,int,int], List[Tuple[int,int,str,str]]]
                                ) -> List[Tuple[int,int,str,Dict[str,Any]]]:
        olist = overrides.get(verse_key, [])
        if not olist:
            return spans
        base = spans[:]
        for (s, e, tag, note) in olist:
            injected = (int(s), int(e), str(tag), {"source":"override", "note": note})
            base = [sp for sp in base if not (max(sp[0], s) < min(sp[1], e))]
            base.append(injected)
        base.sort(key=lambda x: (x[0], x[1]))
        return base

    @staticmethod
    def _row_to_verse(row) -> "VerseRow":
        return VerseRow(id=row[0], book=row[1], chapter=row[2], verse_num=row[3], text_plain=row[4])

    @staticmethod
    def _row_to_token(row) -> "TokenRow":
        return TokenRow(id=row[0], verse_id=row[1], token_idx=row[2], text=row[3],
                        strong_norm=row[4], morph_norm=row[5], italics=bool(row[6]))

    @staticmethod
    def fetch_verse(con: sqlite3.Connection, verse_id: int) -> "VerseRow":
        cur = con.cursor()
        cur.execute("""
            SELECT id, book, chapter, verse_num, text_plain
            FROM verses
            WHERE id = ?
        """, (verse_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Verse id {verse_id} not found")
        return BibleNLP._row_to_verse(row)

    @staticmethod
    def fetch_tokens_for_verse(con: sqlite3.Connection, verse_id: int) -> List["TokenRow"]:
        cur = con.cursor()
        cur.execute("""
            SELECT id, verse_id, token_idx, text, strong_norm, morph_norm, italics
            FROM tokens
            WHERE verse_id = ?
            ORDER BY token_idx ASC
        """, (verse_id,))
        return [BibleNLP._row_to_token(r) for r in cur.fetchall()]

    @staticmethod
    def iter_verses(con: sqlite3.Connection, book_filter: Optional[str] = None) -> Iterable["VerseRow"]:
        cur = con.cursor()
        if book_filter:
            cur.execute("""
                SELECT id, book, chapter, verse_num, text_plain
                FROM verses
                WHERE book = ?
                ORDER BY book, chapter, verse_num
            """, (book_filter,))
        else:
            cur.execute("""
                SELECT id, book, chapter, verse_num, text_plain
                FROM verses
                ORDER BY book, chapter, verse_num
            """)
        for row in cur.fetchall():
            yield BibleNLP._row_to_verse(row)

    @staticmethod
    def annotate_verse_with_hybrid(con: sqlite3.Connection,
                                verse: "VerseRow",
                                strongs_map: Dict[str, Dict[str, str]],
                                nlp,
                                overrides: Dict[Tuple[str,int,int], List[Tuple[int,int,str,str]]],
                                priority: Tuple[str,str] = ("strongs","gazetteer"),
                                merge_multiword: bool = True
                                ) -> List[Tuple[int,int,str,Dict[str,Any]]]:
        tokens = BibleNLP.fetch_tokens_for_verse(con, verse.id)
        s_spans = BibleNLP.spans_from_strongs(tokens, verse.text_plain, strongs_map, prefer_multiword_merge=merge_multiword)
        g_spans = BibleNLP.spans_from_gazetteer(nlp, verse.text_plain)
        spans = BibleNLP.merge_spans_with_priority(s_spans, g_spans, priority=priority)
        spans = BibleNLP.apply_overrides_to_spans(spans, (verse.book, verse.chapter, verse.verse_num), overrides)
        return spans

    @staticmethod
    def export_silver_jsonl(db_path: str,
                            out_jsonl: str,
                            strongs_map_path: Optional[str],
                            gazetteer_dir: Optional[str],
                            overrides_db_path: Optional[str] = None,
                            overrides_json_path: Optional[str] = None,
                            book_filter: Optional[str] = None,
                            overwrite_ents: bool = True,
                            case_sensitive_gazetteers: bool = True,
                            priority: Tuple[str,str] = ("strongs","gazetteer"),
                            merge_multiword: bool = True) -> Dict[str, Any]:
        con = sqlite3.connect(db_path)
        try:
            strongs_map = BibleNLP.load_strongs_entity_map(strongs_map_path) if strongs_map_path else {}
            patterns = BibleNLP.load_gazetteer_patterns_from_dir(gazetteer_dir) if gazetteer_dir else []
            nlp = BibleNLP.build_nlp_with_gazetteers(patterns, overwrite_ents=overwrite_ents,
            # Load multi-label lookup for exporter (from gazetteer_dir if available)
            ml_lookup = None
            try:
                base_dir = gazetteer_dir or CONFIG.get('entity_dir','bible_entities')
                for cand in ('DEITY_master_KJV.json','DEITY_with_multilabel_context.json','DEITY.json'):
                    cand_path = os.path.join(base_dir, cand)
                    if os.path.exists(cand_path):
                        ml_lookup = load_multilabel_lookup(cand_path)
                        break
            except Exception:
                ml_lookup = None
                                                    case_sensitive=case_sensitive_gazetteers)
            overrides = BibleNLP.load_overrides(db_path=overrides_db_path, json_path=overrides_json_path)

            outp = Path(out_jsonl)
            outp.parent.mkdir(parents=True, exist_ok=True)
            total = 0
            with outp.open("w", encoding="utf-8") as fw:
                for verse in BibleNLP.iter_verses(con, book_filter=book_filter):
                    spans = BibleNLP.annotate_verse_with_hybrid(con, verse, strongs_map, nlp, overrides,
                                                                priority=priority, merge_multiword=merge_multiword)
                    obj = {
                        "book": verse.book,
                        "chapter": verse.chapter,
                        "verse": verse.verse_num,
                        "text": verse.text_plain,
                        "spans": [{"start": s, "end": e, "label": tag, "meta": meta} for (s,e,tag,meta) in spans]
                    }
                    fw.write(json.dumps(obj, ensure_ascii=False) + "\n")
                    total += 1
            return {"ok": True, "verses": total, "out": str(outp.resolve())}
        finally:
            try:
                con.close()
            except Exception:
                pass