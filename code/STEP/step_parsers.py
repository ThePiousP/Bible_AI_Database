#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step_parsers.py
Data structures and HTML parsers for STEP chapter data

BEFORE (Phase 1):
  - Parser functions in step_adapter.py (lines 487-1018)
  - No type hints on data classes
  - Mixed parser logic

AFTER (Phase 2):
  - Dedicated parsers module
  - Full type hints on dataclasses
  - Separated selectolax vs BS4 parsers
  - Better error handling
  - Clear documentation

Created: 2025-10-29 (Phase 2 Refactoring)
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path

# Import alignment utilities
from step_alignment import collapse, tidy_punct, align_text_offsets, vfrag_offsets
from step_normalization import normalize_strongs, normalize_morph, decode_morph


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class Token:
    """
    Represents a single word/token from STEP HTML with linguistic annotations.

    Attributes:
        text: Display text of the token
        strong_norm: Normalized Strong's number (e.g., "H0430", "G2316")
        strong_raw: Raw Strong's attribute from HTML
        morph_norm: Normalized morphology code
        morph_raw: Raw morphology attribute from HTML
        italics: Whether token appears in italics (supplied words)

        html_start: Document-level character offset (start)
        html_end: Document-level character offset (end)
        vhtml_start: Verse-relative HTML offset (start)
        vhtml_end: Verse-relative HTML offset (end)

        morph_gloss: Human-readable morphology description
        morph_features: Structured morphology features dict

        lemma: Strong's lexicon lemma (original language)
        transliteration: Romanized pronunciation
        pronunciation: Phonetic pronunciation
        pos: Part of speech
        definition: Strong's definition
        kjv_translation_count: Raw KJV translation count string
        kjv_counts: Structured KJV counts (parsed)
        etymology: Etymology information
        outline: Outline of biblical usage

        text_start: Plain text character offset (start)
        text_end: Plain text character offset (end)
        token_id: Unique token identifier (e.g., "Gen.1.1#t0000")
    """
    text: str
    strong_norm: Optional[str] = None
    strong_raw: Optional[str] = None
    morph_norm: Optional[str] = None
    morph_raw: Optional[str] = None
    italics: bool = False

    # Document-level offsets (whole HTML)
    html_start: Optional[int] = None
    html_end: Optional[int] = None

    # Verse-relative offsets (fragment within verse_html)
    vhtml_start: Optional[int] = None
    vhtml_end: Optional[int] = None

    # Morph decoding
    morph_gloss: Optional[str] = None
    morph_features: Optional[Dict[str, Any]] = None

    # Strong's lexicon enrichment
    lemma: Optional[str] = None
    transliteration: Optional[str] = None
    pronunciation: Optional[str] = None
    pos: Optional[str] = None
    definition: Optional[str] = None
    kjv_translation_count: Optional[str] = None
    kjv_counts: Optional[List[Dict[str, Any]]] = None
    etymology: Optional[str] = None
    outline: Optional[List[str]] = None

    # Runtime alignment
    text_start: Optional[int] = None
    text_end: Optional[int] = None
    token_id: Optional[str] = None


@dataclass
class Footnote:
    """
    Represents a footnote/cross-reference from STEP HTML.

    Attributes:
        marker: Footnote marker character (e.g., 'a', 'b', '1')
        notetype: Type of note (e.g., "xref", "textual", "translation")
        ref_attr: Reference attribute from <a> tag
        xref_attr: Cross-reference attribute from <a> tag
        body_text: Plain text of footnote body
        body_html: HTML of footnote body
    """
    marker: Optional[str]
    notetype: Optional[str]
    ref_attr: Optional[str]
    xref_attr: Optional[str]
    body_text: Optional[str]
    body_html: Optional[str]


@dataclass
class Verse:
    """
    Represents a single verse with tokens and footnotes.

    Attributes:
        ref: OSIS reference (e.g., "Gen.1.1")
        verse_num: Verse number within chapter
        text_plain: Plain text of verse (no HTML)
        verse_html: Raw HTML of verse
        tokens: List of Token objects
        footnotes: List of Footnote objects
    """
    ref: Optional[str]
    verse_num: Optional[int]
    text_plain: Optional[str]
    verse_html: Optional[str]
    tokens: List[Token]
    footnotes: List[Footnote]


# ============================================================================
# Helper: Plain Text Extraction
# ============================================================================

def _node_has_ancestor_with_class(node, class_name: str) -> bool:
    """Check if node has ancestor with given class (selectolax)."""
    cur = getattr(node, "parent", None)
    while cur is not None:
        cls = (cur.attributes.get("class") or "") if hasattr(cur, "attributes") else ""
        if class_name in cls.split():
            return True
        cur = getattr(cur, "parent", None)
    return False


# ============================================================================
# Selectolax Parser
# ============================================================================

def parse_with_selectolax(html: str, include_italics: bool = True) -> List[Verse]:
    """
    Parse STEP-style chapter HTML using selectolax (fast).

    - Emits Tokens from spans with strong/morph attributes
    - Optionally emits italics-only Tokens for <em> elements
    - vhtml_* are verse-relative offsets; html_* are document-level

    Args:
        html: Full chapter HTML
        include_italics: Whether to include italics tokens

    Returns:
        List of Verse objects

    Raises:
        ImportError: If selectolax is not installed
    """
    from selectolax.parser import HTMLParser, Node

    def _immediate_em_children(sp: Node) -> List[Node]:
        """Get immediate <em> children of span."""
        try:
            return [c for c in (sp.children or []) if getattr(c, "tag", None) == "em"]
        except Exception:
            return []

    def plain_text_from_verse(v: Node) -> str:
        """Extract plain text from verse node."""
        chunks: List[str] = []
        for child in v.iter():
            tag = getattr(child, "tag", None)
            if tag != "-text-":
                cls = child.attributes.get("class", "")
                # Skip nested verse containers, verse numbers, notes
                if child is not v and tag == "span" and "verse" in cls:
                    continue
                if "verseNumber" in cls:
                    continue
                if tag == "sup" and "note" in cls:
                    continue
                if tag == "a" and child.attributes.get("class") == "verseLink":
                    continue
                continue

            # Text node
            if _node_has_ancestor_with_class(child, "verseNumber"):
                continue
            par = getattr(child, "parent", None)
            if par and par.tag == "sup" and "note" in (par.attributes.get("class") or ""):
                continue

            t = collapse(child.text())
            if t:
                chunks.append(t)

        return tidy_punct(collapse(" ".join(chunks)))

    tree = HTMLParser(html)
    verses: List[Verse] = []
    doc_cursor = 0  # Global doc cursor for html_* offsets

    for v in tree.css("span.verse"):
        # Extract reference
        a = v.css_first("a.verseLink[name]")
        ref = a.attributes.get("name") if a and "name" in a.attributes else None

        verse_html = v.html
        verse_cursor = 0  # Verse-relative cursor

        # Verse number
        vn_node = v.css_first(".verseNumber")
        try:
            verse_num = int(vn_node.text().strip()) if vn_node else None
        except Exception:
            verse_num = None

        tokens: List[Token] = []
        emitted_frags: set = set()

        # Parse semantic spans with strong/morph
        for sp in v.css("span"):
            if "note" in (sp.attributes.get("class") or ""):
                continue

            strong_raw = sp.attributes.get("strong")
            morph_raw = sp.attributes.get("morph")
            direct_ems = _immediate_em_children(sp)

            if strong_raw or morph_raw:
                text_val = collapse(sp.text())
                strong_norm, strong_raw_keep = normalize_strongs(strong_raw)
                morph_norm, morph_raw_keep = normalize_morph(morph_raw)
                morph_gloss, morph_features = decode_morph(morph_norm, morph_raw_keep)

                italics_local = bool(direct_ems)
                frag = sp.html
                vs, ve, verse_cursor = vfrag_offsets(frag, verse_html, verse_cursor)

                # Doc-level offsets
                ds = de = None
                if frag:
                    i = html.find(frag, doc_cursor)
                    if i == -1:
                        i = html.find(frag)
                    if i != -1:
                        ds, de = i, i + len(frag)
                        doc_cursor = de

                tokens.append(Token(
                    text=text_val,
                    strong_norm=strong_norm,
                    strong_raw=strong_raw_keep,
                    morph_norm=morph_norm,
                    morph_raw=morph_raw_keep,
                    italics=italics_local,
                    html_start=ds,
                    html_end=de,
                    vhtml_start=vs,
                    vhtml_end=ve,
                    morph_gloss=morph_gloss,
                    morph_features=morph_features
                ))
                if frag:
                    emitted_frags.add(frag)

            # Italics-only tokens (immediate <em> children)
            if include_italics and direct_ems:
                for em in direct_ems:
                    t = collapse(em.text())
                    frag_em = em.html
                    if not t or not frag_em:
                        continue

                    vs_em, ve_em, verse_cursor = vfrag_offsets(frag_em, verse_html, verse_cursor)

                    ds_em = de_em = None
                    i2 = html.find(frag_em, doc_cursor)
                    if i2 == -1:
                        i2 = html.find(frag_em)
                    if i2 != -1:
                        ds_em, de_em = i2, i2 + len(frag_em)
                        doc_cursor = de_em

                    tokens.append(Token(
                        text=t,
                        italics=True,
                        html_start=ds_em,
                        html_end=de_em,
                        vhtml_start=vs_em,
                        vhtml_end=ve_em
                    ))
                    emitted_frags.add(frag_em)

        # Catch-all for stray <em> (not already emitted)
        if include_italics:
            for em in v.css("em"):
                frag_em = em.html
                if not frag_em or frag_em in emitted_frags:
                    continue
                t = collapse(em.text())
                if not t:
                    continue

                vs_em, ve_em, verse_cursor = vfrag_offsets(frag_em, verse_html, verse_cursor)

                ds_em = de_em = None
                i2 = html.find(frag_em, doc_cursor)
                if i2 == -1:
                    i2 = html.find(frag_em)
                if i2 != -1:
                    ds_em, de_em = i2, i2 + len(frag_em)
                    doc_cursor = de_em

                tokens.append(Token(
                    text=t,
                    italics=True,
                    html_start=ds_em,
                    html_end=de_em,
                    vhtml_start=vs_em,
                    vhtml_end=ve_em
                ))
                emitted_frags.add(frag_em)

        # Parse footnotes
        footnotes: List[Footnote] = []
        for sup in v.css("sup.note"):
            a = sup.css_first("a[notetype]")
            body = sup.css_first(".inlineNote")
            marker_text = sup.text().strip()
            marker = marker_text[:1] if marker_text else None
            footnotes.append(Footnote(
                marker=marker,
                notetype=a.attributes.get("notetype") if a else None,
                ref_attr=a.attributes.get("ref") if a and "ref" in a.attributes else None,
                xref_attr=a.attributes.get("xref") if a and "xref" in a.attributes else None,
                body_text=collapse(body.text()) if body else None,
                body_html=body.html if body else None
            ))

        # Assign stable token IDs
        for i, tok in enumerate(tokens):
            tok.token_id = f"{ref}#t{i:04d}" if ref else f"t{i:04d}"

        # Compute text offsets
        plain = plain_text_from_verse(v)
        align_text_offsets(plain, tokens)

        verses.append(Verse(
            ref=ref,
            verse_num=verse_num,
            text_plain=plain,
            verse_html=verse_html,
            tokens=tokens,
            footnotes=footnotes
        ))

    return verses


# ============================================================================
# BeautifulSoup Parser
# ============================================================================

def parse_with_bs4(html: str, include_italics: bool = True) -> List[Verse]:
    """
    Parse STEP-style chapter HTML using BeautifulSoup (fallback).

    Mirrors selectolax semantics.

    Args:
        html: Full chapter HTML
        include_italics: Whether to include italics tokens

    Returns:
        List of Verse objects

    Raises:
        ImportError: If BeautifulSoup4 is not installed
    """
    from bs4 import BeautifulSoup, NavigableString, Tag

    def plain_text_from_verse(v: Tag) -> str:
        """Extract plain text from verse."""
        chunks: List[str] = []
        for node in v.descendants:
            if isinstance(node, NavigableString):
                parent = node.parent
                if parent and parent.name == "sup" and parent.get("class") and "note" in parent.get("class"):
                    continue
                t = collapse(str(node))
                if t:
                    chunks.append(t)
            elif isinstance(node, Tag):
                cls = node.get("class") or []
                if node is not v and node.name == "span" and "verse" in cls:
                    continue
                if node.name == "a" and node.get("class") == ["verseLink"]:
                    continue
        return tidy_punct(collapse(" ".join(chunks)))

    soup = BeautifulSoup(html, "html.parser")
    verses: List[Verse] = []
    doc_cursor = 0

    for v in soup.select("span.verse"):
        a = v.select_one("a.verseLink[name]")
        ref = a["name"] if a and a.has_attr("name") else None

        verse_html = str(v)
        verse_cursor = 0

        vn = v.select_one(".verseNumber")
        try:
            verse_num = int(vn.get_text(strip=True)) if vn else None
        except Exception:
            verse_num = None

        tokens: List[Token] = []
        emitted_frags: set = set()

        for sp in v.find_all("span"):
            if sp.get("class") and "note" in sp.get("class"):
                continue

            strong_raw = sp.get("strong")
            morph_raw = sp.get("morph")
            direct_ems = sp.find_all("em", recursive=False)

            if strong_raw or morph_raw:
                text_val = collapse(sp.get_text(" ", strip=True))
                strong_norm, strong_raw_keep = normalize_strongs(strong_raw)
                morph_norm, morph_raw_keep = normalize_morph(morph_raw)
                morph_gloss, morph_features = decode_morph(morph_norm, morph_raw_keep)

                italics_local = bool(direct_ems)
                frag = str(sp)
                vs, ve, verse_cursor = vfrag_offsets(frag, verse_html, verse_cursor)

                ds = de = None
                if frag:
                    i = html.find(frag, doc_cursor)
                    if i == -1:
                        i = html.find(frag)
                    if i != -1:
                        ds, de = i, i + len(frag)
                        doc_cursor = de

                tokens.append(Token(
                    text=text_val,
                    strong_norm=strong_norm,
                    strong_raw=strong_raw_keep,
                    morph_norm=morph_norm,
                    morph_raw=morph_raw_keep,
                    italics=italics_local,
                    html_start=ds,
                    html_end=de,
                    vhtml_start=vs,
                    vhtml_end=ve,
                    morph_gloss=morph_gloss,
                    morph_features=morph_features
                ))
                emitted_frags.add(frag)

            # Italics-only tokens
            if include_italics and direct_ems:
                for em in direct_ems:
                    t = collapse(em.get_text(" ", strip=True))
                    frag_em = str(em)
                    if not t or not frag_em:
                        continue

                    vs_em, ve_em, verse_cursor = vfrag_offsets(frag_em, verse_html, verse_cursor)

                    ds_em = de_em = None
                    i2 = html.find(frag_em, doc_cursor)
                    if i2 == -1:
                        i2 = html.find(frag_em)
                    if i2 != -1:
                        ds_em, de_em = i2, i2 + len(frag_em)
                        doc_cursor = de_em

                    tokens.append(Token(
                        text=t,
                        italics=True,
                        html_start=ds_em,
                        html_end=de_em,
                        vhtml_start=vs_em,
                        vhtml_end=ve_em
                    ))
                    emitted_frags.add(frag_em)

        # Catch-all for stray <em>
        if include_italics:
            for em in v.find_all("em"):
                frag_em = str(em)
                if frag_em in emitted_frags:
                    continue
                t = collapse(em.get_text(" ", strip=True))
                if not t:
                    continue

                vs_em, ve_em, verse_cursor = vfrag_offsets(frag_em, verse_html, verse_cursor)

                ds_em = de_em = None
                i2 = html.find(frag_em, doc_cursor)
                if i2 == -1:
                    i2 = html.find(frag_em)
                if i2 != -1:
                    ds_em, de_em = i2, i2 + len(frag_em)
                    doc_cursor = de_em

                tokens.append(Token(
                    text=t,
                    italics=True,
                    html_start=ds_em,
                    html_end=de_em,
                    vhtml_start=vs_em,
                    vhtml_end=ve_em
                ))
                emitted_frags.add(frag_em)

        # Footnotes
        footnotes: List[Footnote] = []
        for sup in v.select("sup.note, sup[class*=note]"):
            a = sup.select_one("a[notetype]")
            inline = sup.select_one(".inlineNote, .noteBody, .note-content")
            marker_text = sup.get_text(strip=True)
            marker = marker_text[:1] if marker_text else None
            footnotes.append(Footnote(
                marker=marker,
                notetype=a.get("notetype") if a else None,
                ref_attr=a.get("ref") if a and a.has_attr("ref") else None,
                xref_attr=a.get("xref") if a and a.has_attr("xref") else None,
                body_text=collapse(inline.get_text(" ", strip=True)) if inline else None,
                body_html=str(inline) if inline else None
            ))

        # Token IDs
        for i, tok in enumerate(tokens):
            tok.token_id = f"{ref}#t{i:04d}" if ref else f"t{i:04d}"

        plain = plain_text_from_verse(v)
        align_text_offsets(plain, tokens)

        verses.append(Verse(
            ref=ref,
            verse_num=verse_num,
            text_plain=plain,
            verse_html=verse_html,
            tokens=tokens,
            footnotes=footnotes
        ))

    return verses


# ============================================================================
# Unified Parser Interface
# ============================================================================

def parse_step_html(
    html: str,
    include_italics: bool = True,
    parser: str = "auto",
    verbose: bool = False
) -> List[Verse]:
    """
    Parse STEP HTML using selectolax or BeautifulSoup.

    Args:
        html: Full chapter HTML
        include_italics: Include italics tokens
        parser: "auto", "selectolax", or "bs4"
        verbose: Print warnings

    Returns:
        List of Verse objects

    Raises:
        ImportError: If required parser library not installed
    """
    if parser not in ("auto", "selectolax", "bs4"):
        parser = "auto"

    if parser in ("auto", "selectolax"):
        try:
            import selectolax  # noqa
            return parse_with_selectolax(html, include_italics=include_italics)
        except Exception as e:
            if verbose:
                print(f"[warn] selectolax failed: {e.__class__.__name__}: {e}")
            if parser == "selectolax":
                raise

    return parse_with_bs4(html, include_italics=include_italics)


if __name__ == "__main__":
    print("STEP Parsers Module")
    print("=" * 60)
    print(f"Data classes defined: Token, Footnote, Verse")
    print(f"Parsers available: selectolax, bs4")
    print("\n✓ Parsers module loaded successfully!")
