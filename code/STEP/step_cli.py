#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step_cli.py
Interactive menu interface for STEP adapter

BEFORE (Phase 1):
  - Menu functions in step_adapter.py (lines 1261-1409)
  - No type hints
  - Mixed with main logic

AFTER (Phase 2):
  - Dedicated CLI module
  - Full type hints
  - Better input handling
  - Clearer menu structure

Created: 2025-10-29 (Phase 2 Refactoring)
"""

import os
from pathlib import Path
from typing import Optional

# Import from other STEP modules
from step_export import export_chapter, batch_export_book, batch_export_full_bible, build_url
from step_constants import resolve_book_code


# ============================================================================
# Configuration Management
# ============================================================================

def load_config() -> dict:
    """
    Load configuration from step_config.py (if available).

    Returns:
        Configuration dictionary with defaults
    """
    try:
        from step_config import load_config as _load_config
        return _load_config()
    except ImportError:
        # Return defaults if step_config.py doesn't exist
        return {
            "parser_default": "auto",
            "include_italics_default": True,
            "version_default": "KJV",
            "options_default": "NHVUG",
            "output_dir": "output/json",
            "log_dir": "output/logs",
            "continue_on_error": True,
            "batch_defaults": {"start_chapter": 1, "end_chapter": 50},
        }


def set_field(key: str, value) -> dict:
    """
    Update a configuration field.

    Args:
        key: Configuration key
        value: New value

    Returns:
        Updated configuration dictionary
    """
    try:
        from step_config import set_field as _set_field
        return _set_field(key, value)
    except ImportError:
        # If no step_config.py, just return load_config() defaults
        return load_config()


# ============================================================================
# Input Helpers
# ============================================================================

def prompt(msg: str, default: Optional[str] = None) -> str:
    """
    Prompt user for input with optional default.

    Args:
        msg: Prompt message
        default: Default value if user presses Enter

    Returns:
        User input string (or default)

    Example:
        >>> prompt("Enter name", "John")
        Enter name [John]: <user presses Enter>
        'John'
    """
    p = f"{msg}"
    if default is not None:
        p += f" [{default}]"
    p += ": "
    val = input(p).strip()
    return val if val else (default or "")


def yn(msg: str, default: bool) -> bool:
    """
    Prompt user for yes/no input.

    Args:
        msg: Prompt message
        default: Default value (True=Y, False=N)

    Returns:
        Boolean response

    Example:
        >>> yn("Continue?", True)
        Continue? (Y/n): y
        True
    """
    d = "Y/n" if default else "y/N"
    ans = input(f"{msg} ({d}): ").strip().lower()
    if not ans:
        return default
    return ans in ("y", "yes", "1", "true", "t")


# ============================================================================
# Settings Menu
# ============================================================================

def settings_menu() -> None:
    """
    Display settings menu and allow user to change configuration.

    Modifies configuration using set_field() function.
    """
    cfg = load_config()

    while True:
        print("\n=== Settings ===")
        print(f" 1) Parser default         : {cfg['parser_default']}")
        print(f" 2) Include italics default: {cfg['include_italics_default']}")
        print(f" 3) Version default        : {cfg['version_default']}")
        print(f" 4) Options default        : {cfg['options_default']}")
        print(f" 5) Output dir             : {cfg['output_dir']}")
        print(f" 6) Log dir                : {cfg['log_dir']}")
        print(f" 7) HTML cache dir         : {cfg['html_cache_dir']}")
        print(f" 8) Continue on error      : {cfg['continue_on_error']}")
        print(f" 9) Batch start chapter    : {cfg['batch_defaults']['start_chapter']}")
        print(f"10) Batch end chapter      : {cfg['batch_defaults']['end_chapter']}")
        print(" 0) Back")

        choice = input("> ").strip()

        if choice == "1":
            val = prompt("Parser (auto/selectolax/bs4)", cfg["parser_default"])
            if val in ("auto", "selectolax", "bs4"):
                cfg = set_field("parser_default", val)

        elif choice == "2":
            cfg = set_field(
                "include_italics_default",
                yn("Include italics tokens by default?", cfg["include_italics_default"])
            )

        elif choice == "3":
            cfg = set_field("version_default", prompt("Version code", cfg["version_default"]))

        elif choice == "4":
            cfg = set_field("options_default", prompt("STEP options string", cfg["options_default"]))

        elif choice == "5":
            cfg = set_field("output_dir", prompt("Output directory", cfg["output_dir"]))

        elif choice == "6":
            cfg = set_field("log_dir", prompt("Log directory", cfg["log_dir"]))

        elif choice == "7":
            cfg = set_field("html_cache_dir", prompt("HTML cache directory", cfg["html_cache_dir"]))

        elif choice == "8":
            cfg = set_field(
                "continue_on_error",
                yn("Continue on errors during batch?", cfg["continue_on_error"])
            )

        elif choice == "9":
            try:
                start = int(prompt("Batch start chapter", str(cfg["batch_defaults"]["start_chapter"])))
                bd = cfg["batch_defaults"].copy()
                bd["start_chapter"] = start
                cfg = set_field("batch_defaults", bd)
            except ValueError:
                print("Enter a number.")

        elif choice == "10":
            try:
                end = int(prompt("Batch end chapter", str(cfg["batch_defaults"]["end_chapter"])))
                bd = cfg["batch_defaults"].copy()
                bd["end_chapter"] = end
                cfg = set_field("batch_defaults", bd)
            except ValueError:
                print("Enter a number.")

        elif choice == "0":
            break

        else:
            print("Pick 0–10.")


# ============================================================================
# Run Menu (Main Menu)
# ============================================================================

def run_menu() -> None:
    """
    Display main menu and handle user selections.

    Options:
      1. Export by OSIS ref (fetch via STEP URL)
      2. Export from local STEP HTML file
      3. Batch export a book
      4. Full Bible batch (all 66 books)
      5. Settings
      6. Quit
    """
    cfg = load_config()
    include_italics = cfg["include_italics_default"]
    parser = cfg["parser_default"]
    version = cfg["version_default"]
    options = cfg["options_default"]
    output_dir = cfg["output_dir"]

    while True:
        print("\n=== STEP Adapter ===")
        print("1) Export by OSIS ref (fetch via STEP URL)")
        print("2) Export from a local STEP HTML file")
        print("3) Batch export a book")
        print("4) Full Bible batch (ALL books/chapters)")
        print("5) Settings")
        print("6) Quit")

        choice = input("> ").strip()

        if choice == "1":
            # Export by OSIS ref (URL fetch)
            ref = prompt("OSIS ref (e.g., Gen.22)", "Gen.22")
            out_default = str((Path(output_dir) / f"{ref}.json").resolve())
            out_path = prompt("Output JSON path", out_default)
            url = build_url(version, ref, options)

            print("\nExporting...")
            payload = export_chapter(
                url,
                out_path,
                include_italics=include_italics,
                parser=parser,
                verbose=True
            )
            print(f"Done. Verses: {payload['verse_count']}\nSaved: {out_path}\n")

        elif choice == "2":
            # Export from local HTML file
            infile = prompt("Path to saved STEP HTML (e.g., STEP_Gen22.html)", "STEP_Gen22.html")
            if not os.path.exists(infile):
                print("File not found. Try again.\n")
                continue

            ref_guess = Path(infile).stem.replace("STEP_", "")
            out_default = str((Path(output_dir) / f"{ref_guess}.json").resolve())
            out_path = prompt("Output JSON path", out_default)

            print("\nExporting...")
            payload = export_chapter(
                infile,
                out_path,
                include_italics=include_italics,
                parser=parser,
                verbose=True
            )
            print(f"Done. Verses: {payload['verse_count']}\nSaved: {out_path}\n")

        elif choice == "3":
            # Batch export a single book
            book_input = prompt("Book code or name (e.g., Gen, Jude, Judges)", "Gen")
            book_code = resolve_book_code(book_input)

            if not book_code:
                print(f"ERROR: Could not resolve '{book_input}' to a valid book.")
                print("Try: Full name (Genesis, Jude), OSIS code (Gen, Jude), or unique prefix")
                continue

            print(f"Resolved '{book_input}' to OSIS code: {book_code}")

            source_mode = prompt("Source mode: url/file", "url")
            start = int(prompt("Start chapter", str(cfg["batch_defaults"]["start_chapter"])))
            end = int(prompt("End chapter", str(cfg["batch_defaults"]["end_chapter"])))
            html_dir = prompt("Local HTML dir (used if source=file)", cfg["html_cache_dir"])

            res = batch_export_book(
                book=book_code,
                start=start,
                end=end,
                source_mode=source_mode,
                version=version,
                options=options,
                html_dir=html_dir,
                output_dir=output_dir,
                include_italics=include_italics,
                parser=parser,
                continue_on_error=cfg["continue_on_error"],
                log_dir=cfg["log_dir"],
                verbose=True
            )
            print(f"Batch finished. OK={len(res['ok'])}, Failed={len(res['failed'])}")
            print(f"Log: {res['log']}")

        elif choice == "4":
            # Full Bible batch (all 66 books)
            source_mode = prompt("Source mode: url/file", "url")
            html_dir = prompt("Local HTML dir (used if source=file)", cfg["html_cache_dir"])

            print("\nExporting FULL BIBLE...")
            res = batch_export_full_bible(
                source_mode=source_mode,
                version=version,
                options=options,
                html_dir=html_dir,
                output_dir=output_dir,
                include_italics=include_italics,
                parser=parser,
                continue_on_error=cfg["continue_on_error"],
                log_dir=cfg["log_dir"],
                verbose=True
            )
            print(f"Full Bible batch finished. OK={len(res['ok'])}, Failed={len(res['failed'])}")
            print(f"Log: {res['log']}")

        elif choice == "5":
            # Settings menu
            settings_menu()
            cfg = load_config()
            include_italics = cfg["include_italics_default"]
            parser = cfg["parser_default"]
            version = cfg["version_default"]
            options = cfg["options_default"]
            output_dir = cfg["output_dir"]

        elif choice == "6":
            # Quit
            print("Goodbye!")
            break

        else:
            print("Pick 1–6.")


if __name__ == "__main__":
    print("STEP CLI Module")
    print("=" * 60)
    print("Interactive menu system for STEP adapter")
    print("\n✓ CLI module loaded successfully!")
    print("\nRun run_menu() to start the interactive interface.")
