#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive wrapper for export_ner_silver.py with presets, dry-run checks,
batch mode, last-run caching — plus Tools submenu:
  • Audit current dataset (dataset_audit.py)
  • Generate PERSON/PLACE candidate lists (propose_label_candidates.py)
  • Train baseline spaCy model (train_baseline_spacy.py)
  • Backfill Strong's lexicon (backfill_strongs_lexicon.py)

Return to the main menu from any submenu.

Usage:
  python silver_menu.py
"""

from __future__ import annotations

import os
import sys
import yaml
import shlex
import sqlite3
import platform
import subprocess
from typing import Dict, Any, List, Optional

# ----------------------------
# Constants / defaults 
# ----------------------------
CONFIG_FILE = "silver_config.yml"
LAST_RUN_FILE = ".silver_last_run.yml"

OS_IS_WINDOWS = platform.system().lower().startswith("win")
DEFAULT_DB = r"C:\BIBLE\concordance.db" if OS_IS_WINDOWS else "./concordance.db"
DEFAULT_RULES = "./label_rules.yml"
DEFAULT_OUTDIR = "./silver_out"
DEFAULT_EXPORTER = "./export_ner_silver.py"

# Tools (optional scripts)
DEFAULT_DATASET_AUDIT      = "./dataset_audit.py"
DEFAULT_PROPOSE_CANDS      = "./propose_label_candidates.py"
DEFAULT_SPACY_TRAIN        = "./train_baseline_spacy.py"
DEFAULT_BACKFILL_LEXICON   = "./backfill_strongs_lexicon.py"

DEFAULT_CONFIG: Dict[str, Any] = {
    "defaults": {
        "exporter_path": DEFAULT_EXPORTER,
        "db": "auto",              # "auto" chooses OS default
        "rules": DEFAULT_RULES,
        "outdir": DEFAULT_OUTDIR,
        "seed": 40,
        "ratios": [0.8, 0.1, 0.1],
        "holdout_books": [],
        "holdout_name": "domain_holdout",
        "logging": "info",         # quiet|info|debug (wrapper verbosity)
        "dry_run": False,
        "text_prefer": "auto",
        "overwrite": False,
        # NEW: fallback label control for unmatched tokens (None → don't pass flag)
        # Recommended values: "NONE" to disable fallback, or a label like "OTHER"
        "label_on_miss": None,

        # Tool paths (you may customize these in Settings)
        "dataset_audit_path": DEFAULT_DATASET_AUDIT,
        "propose_candidates_path": DEFAULT_PROPOSE_CANDS,
        "spacy_trainer_path": DEFAULT_SPACY_TRAIN,
        "backfill_lexicon_path": DEFAULT_BACKFILL_LEXICON
    },
    "profiles": {
        "default": {
            "outdir": "./silver_out"
        },
        "gospels_holdout": {
            "holdout_books": ["Matthew", "Mark", "Luke", "John"],
            "holdout_name": "gospels_eval",
            "outdir": "./silver_out_gospels"
        },
        "ot_only": {
            # placeholder; you can later add filters in exporter and wire them here
            "outdir": "./silver_out_ot"
        }
    }
}


# ----------------------------
# Utils
# ----------------------------
def load_yaml(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return None


def save_yaml(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def ensure_config_exists() -> Dict[str, Any]:
    cfg = load_yaml(CONFIG_FILE)
    if cfg is None:
        # Write default template
        save_yaml(CONFIG_FILE, DEFAULT_CONFIG)
        cfg = DEFAULT_CONFIG
        print(f"Created default config at {CONFIG_FILE}")
    # Backfill any missing keys if user has an older config
    def merge_defaults(dst: Dict[str, Any], src: Dict[str, Any]):
        for k, v in src.items():
            if k not in dst:
                dst[k] = v
            else:
                if isinstance(v, dict) and isinstance(dst[k], dict):
                    merge_defaults(dst[k], v)
    merge_defaults(cfg, DEFAULT_CONFIG)
    return cfg


def load_last_run() -> Optional[Dict[str, Any]]:
    return load_yaml(LAST_RUN_FILE)


def save_last_run(profile_name: str, resolved: Dict[str, Any]) -> None:
    data = {"profile": profile_name, "resolved": resolved}
    save_yaml(LAST_RUN_FILE, data)


def ask(prompt: str, default: Optional[str] = None) -> str:
    if default is not None:
        s = input(f"{prompt} [{default}]: ").strip()
        return s if s else default
    return input(f"{prompt}: ").strip()


def yes_no(prompt: str, default: bool = False) -> bool:
    d = "Y/n" if default else "y/N"
    s = input(f"{prompt} ({d}): ").strip().lower()
    if not s:
        return default
    return s in ("y", "yes")


def resolve_auto_paths(val: str) -> str:
    if isinstance(val, str) and val.lower() == "auto":
        return DEFAULT_DB
    return val


def validate_paths(db: str, rules: str, exporter_path: str, outdir: str, overwrite: bool) -> List[str]:
    errs: List[str] = []
    if not os.path.exists(exporter_path):
        errs.append(f"Exporter not found: {exporter_path}")
    if not os.path.exists(db):
        errs.append(f"DB not found: {db}")
    if not os.path.exists(rules):
        errs.append(f"Rules file not found: {rules}")
    if os.path.isdir(outdir):
        existing = [fn for fn in os.listdir(outdir) if fn.endswith(".jsonl")]
        if existing and not overwrite:
            errs.append(f"Outdir has existing JSONL files and overwrite=False: {outdir} ({', '.join(existing)})")
    else:
        try:
            os.makedirs(outdir, exist_ok=True)
        except Exception as e:
            errs.append(f"Cannot create outdir: {outdir} ({e})")
    return errs


def make_cmd_args(exporter: str, resolved: Dict[str, Any]) -> List[str]:
    args: List[str] = [sys.executable, exporter]
    args += ["--db", resolved["db"]]
    args += ["--rules", resolved["rules"]]
    args += ["--outdir", resolved["outdir"]]
    if "seed" in resolved and resolved["seed"] is not None:
        args += ["--seed", str(resolved["seed"])]
    if "ratios" in resolved and resolved["ratios"]:
        r = resolved["ratios"]
        if isinstance(r, (list, tuple)) and len(r) == 3:
            args += ["--ratios", str(r[0]), str(r[1]), str(r[2])]
    if "text_prefer" in resolved and resolved["text_prefer"]:
        args += ["--text_prefer", str(resolved["text_prefer"])]
        r = resolved["ratios"]
        if isinstance(r, (list, tuple)) and len(r) == 3:
            args += ["--ratios", str(r[0]), str(r[1]), str(r[2])]
    hb = resolved.get("holdout_books", [])
    if hb:
        args += ["--holdout_books", ",".join(hb)]
        hn = resolved.get("holdout_name", "domain_holdout")
        args += ["--holdout_name", hn]
    # NEW: forward label-on-miss when set
    lom = resolved.get("label_on_miss", None)
    if isinstance(lom, str) and lom.strip():
        args += ["--label-on-miss", lom.strip()]
    return args


def print_rules_summary(rules_path: str) -> None:
    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            rules = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Could not load rules: {e}")
        return

    enabled = rules.get("labels", {}).get("enabled", [])
    disabled = rules.get("labels", {}).get("disabled", [])
    prio = rules.get("conflicts", {}).get("priority", [])

    print("\n=== Label Rules Summary ===")
    print("Enabled:", ", ".join(enabled) if enabled else "(none)")
    print("Disabled:", ", ".join(disabled) if disabled else "(none)")
    if prio:
        print("Priority:", " > ".join(prio))

    rr = rules.get("rules", {})
    for lab in enabled:
        rlab = rr.get(lab, {})
        sids = rlab.get("strongs_ids", []) or []
        lems = rlab.get("lemmas", []) or []
        surfs = rlab.get("surfaces", []) or []
        gzs = rlab.get("gazetteer_files", []) or []
        cs = bool(rlab.get("case_sensitive", True))
        print(f"\n[{lab}]")
        print(f"  Strong's IDs: {len(sids)}")
        if sids[:8]:
            print("    e.g.,", ", ".join(sids[:8]) + (" ..." if len(sids) > 8 else ""))
        print(f"  Lemmas: {len(lems)}")
        if lems[:8]:
            print("    e.g.,", ", ".join(lems[:8]) + (" ..." if len(lems) > 8 else ""))
        print(f"  Surfaces: {len(surfs)}")
        if surfs[:8]:
            print("    e.g.,", ", ".join(surfs[:8]) + (" ..." if len(surfs) > 8 else ""))
        print(f"  Gazetteers: {len(gzs)}")
        if gzs[:4]:
            print("    e.g.,", ", ".join(gzs[:4]) + (" ..." if len(gzs) > 4 else ""))
        print(f"  Case-sensitive: {cs}")
    print()


def dry_run_preview(db_path: str, rules_path: str, resolved: Dict[str, Any], log_level: str) -> None:
    print("\n=== Dry-run preview ===")
    print(f"DB: {db_path}")
    print(f"Rules: {rules_path}")
    print(f"Outdir: {resolved['outdir']}")
    print(f"Ratios: {resolved.get('ratios')}")
    print(f"Text preference: {resolved.get('text_prefer','auto')}")
    print(f"Holdout books: {resolved.get('holdout_books', [])}")
    # NEW: show resolved fallback behavior
    lom = resolved.get("label_on_miss", None)
    if isinstance(lom, str) and lom.strip():
        print(f"Fallback on unmatched tokens: {lom.strip()}")
    else:
        print("Fallback on unmatched tokens: (none / disabled)")

    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            rules = yaml.safe_load(f) or {}
        enabled = rules.get("labels", {}).get("enabled", [])
        print(f"Enabled labels: {enabled}")
    except Exception as e:
        print(f"(Warn) Could not parse rules: {e}")

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
    except Exception as e:
        print(f"(Error) Could not open DB: {e}")
        return

    try:
        def t_exists(name: str) -> bool:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name=?", (name,))
            return cur.fetchone() is not None

        sql = """
            SELECT COUNT(*) AS n
            FROM verses v
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b    ON v.book_id = b.id
        """
        n_verses = conn.execute(sql).fetchone()["n"]
        print(f"Verses (joined): {n_verses}")

        tok_table = None
        for cand in ("tokens_with_lexicon", "vw_tokens_with_lexicon", "tokens_visible", "tokens"):
            if t_exists(cand):
                tok_table = cand
                break
        if tok_table:
            row = conn.execute(f"SELECT COUNT(*) AS n FROM {tok_table}").fetchone()
            print(f"Tokens ({tok_table}): {row['n']}")
        else:
            print("(Warn) No token table found.")
    except Exception as e:
        print(f"(Warn) Preview query failed: {e}")
    finally:
        conn.close()

    print("Dry-run complete. (No files were written.)\n")


def resolve_profile(cfg: Dict[str, Any], profile_name: str) -> Dict[str, Any]:
    defaults = cfg.get("defaults", {})
    profile = cfg.get("profiles", {}).get(profile_name, {})
    resolved = dict(defaults)
    for k, v in profile.items():
        resolved[k] = v
    resolved["db"] = resolve_auto_paths(resolved.get("db", "auto"))
    if isinstance(resolved.get("ratios"), str):
        try:
            parts = [float(x) for x in resolved["ratios"].split("/")]
            if len(parts) == 3:
                resolved["ratios"] = parts
        except Exception:
            pass
    return resolved


def customize_profile_interactive(resolved: Dict[str, Any]) -> Dict[str, Any]:
    exp = ask("Path to exporter", resolved.get("exporter_path", DEFAULT_EXPORTER))
    db = ask("Path to DB", resolved.get("db", DEFAULT_DB))
    rules = ask("Path to rules.yml", resolved.get("rules", DEFAULT_RULES))
    outdir = ask("Output directory", resolved.get("outdir", DEFAULT_OUTDIR))
    ratios_str = ask("Train/Dev/Test ratios (e.g., 0.8/0.1/0.1)",
                     "/".join(str(x) for x in resolved.get("ratios", [0.8, 0.1, 0.1])))
    try:
        ratios = [float(x) for x in ratios_str.split("/")]
        if len(ratios) != 3:
            raise ValueError
    except Exception:
        print("Invalid ratios; keeping previous value.")
        ratios = resolved.get("ratios", [0.8, 0.1, 0.1])

    hb_csv = ask("Holdout books (comma-separated, blank for none)",
                 ",".join(resolved.get("holdout_books", [])))
    holdout_books = [b.strip() for b in hb_csv.split(",") if b.strip()]
    holdout_name = ask("Holdout filename stem", resolved.get("holdout_name", "domain_holdout"))
    text_pref = ask("Text preference (auto|clean|plain)", resolved.get("text_prefer", "auto")).lower()
    if text_pref not in ("auto","clean","plain"):
        text_pref = resolved.get("text_prefer", "auto")
    seed_str = ask("Random seed (int)", str(resolved.get("seed", 13)))
    try:
        seed = int(seed_str)
    except Exception:
        seed = resolved.get("seed", 13)
    overwrite = yes_no("Overwrite existing JSONL if present?", resolved.get("overwrite", False))
    dry_run = yes_no("Dry-run? (no files written)", resolved.get("dry_run", False))
    logging_level = ask("Logging level (quiet|info|debug)", resolved.get("logging", "info")).lower()
    if logging_level not in ("quiet", "info", "debug"):
        logging_level = "info"

    # NEW: fallback behavior prompt (kept simple and explicit)
    lom_default = resolved.get("label_on_miss", None) or "NONE"
    lom = ask('Fallback label for unmatched tokens ("NONE" to disable, or a label like OTHER)', lom_default).strip()
    if not lom:
        lom = "NONE"  # be explicit if user just hits enter
    # Store as a plain string; exporter interprets "NONE" as disabling fallback
    new_resolved = dict(resolved)
    new_resolved.update({
        "text_prefer": text_pref,
        "exporter_path": exp,
        "db": db,
        "rules": rules,
        "outdir": outdir,
        "ratios": ratios,
        "holdout_books": holdout_books,
        "holdout_name": holdout_name,
        "seed": seed,
        "overwrite": overwrite,
        "dry_run": dry_run,
        "logging": logging_level,
        "label_on_miss": lom
    })
    return new_resolved


def stream_subprocess(cmd: List[str]) -> int:
    """Run a subprocess and stream stdout/stderr."""
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=False
        )
    except FileNotFoundError as e:
        print(f"Error launching: {e}")
        return 127

    try:
        stream = proc.stdout
        if stream is None:
            rc = proc.wait()
            print(f"\nProcess finished with code {rc}.")
            return rc
        for line in stream:
            print(line, end="")
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        try:
            proc.terminate()
        except Exception:
            pass
        return 130
    finally:
        rc = proc.wait()
    print(f"\nProcess finished with code {rc}.")
    return rc


def run_export(resolved: Dict[str, Any], profile_name: str) -> None:
    exporter_path = resolved.get("exporter_path", DEFAULT_EXPORTER)
    db = resolved["db"]
    rules = resolved["rules"]
    outdir = resolved["outdir"]
    overwrite = bool(resolved.get("overwrite", False))
    dry = bool(resolved.get("dry_run", False))

    errs = validate_paths(db, rules, exporter_path, outdir, overwrite)
    if errs:
        print("\nValidation errors:")
        for e in errs:
            print(" -", e)
        print("Fix the above or toggle overwrite, then try again.\n")
        return

    if dry:
        dry_run_preview(db, rules, resolved, resolved.get("logging", "info"))
        return

    cmd = make_cmd_args(exporter_path, resolved)
    print("\nRunning exporter:")
    print(" ".join(shlex.quote(c) for c in cmd))
    rc = stream_subprocess(cmd)
    if rc == 0:
        save_last_run(profile_name, resolved)


def select_profile_menu(cfg: Dict[str, Any]) -> Optional[str]:
    profs = list(cfg.get("profiles", {}).keys())
    if not profs:
        print("No profiles defined in silver_config.yml.")
        return None

    print("\n=== Profiles ===")
    for i, name in enumerate(profs, start=1):
        print(f"[{i}] {name}")
    print("[B] Back")
    sel = input("Choose a profile: ").strip().lower()
    if sel in ("b", "back"):
        return None
    try:
        idx = int(sel) - 1
        if 0 <= idx < len(profs):
            return profs[idx]
    except Exception:
        pass
    print("Invalid selection.")
    return None


def batch_run_menu(cfg: Dict[str, Any]) -> None:
    while True:
        profs = list(cfg.get("profiles", {}).keys())
        if not profs:
            print("No profiles defined.")
            return
        print("\n=== Batch Mode ===")
        for i, name in enumerate(profs, start=1):
            print(f"[{i}] {name}")
        print("[B] Back to Main Menu")
        sel = input("Your selection (e.g., 1,3): ").strip().lower()
        if sel in ("b", "back"):
            return

        chosen: List[str] = []
        try:
            for part in sel.split(","):
                part = part.strip()
                if not part:
                    continue
                idx = int(part) - 1
                if 0 <= idx < len(profs):
                    chosen.append(profs[idx])
        except Exception:
            print("Invalid input.")
            continue

        if not chosen:
            print("No profiles chosen.")
            continue

        for p in chosen:
            print(f"\n--- Running profile: {p} ---")
            resolved = resolve_profile(cfg, p)
            errs = validate_paths(resolved["db"], resolved["rules"],
                                  resolved.get("exporter_path", DEFAULT_EXPORTER),
                                  resolved["outdir"],
                                  bool(resolved.get("overwrite", False)))
            if errs:
                print("Validation errors:", errs)
                continue
            run_export(resolved, p)
        print("\nBatch run complete.\n")


def settings_menu(cfg: Dict[str, Any]) -> Dict[str, Any]:
    while True:
        defaults = dict(cfg.get("defaults", {}))
        print("\n=== Settings ===")
        curr_log = defaults.get("logging", "info")
        curr_over = defaults.get("overwrite", False)
        print(f"Logging level: {curr_log}")
        print(f"Overwrite default: {curr_over}")
        new_log = ask("Set logging (quiet|info|debug)", curr_log).lower()
        if new_log not in ("quiet", "info", "debug"):
            new_log = curr_log
        new_over = yes_no("Set overwrite default?", curr_over)
        defaults["logging"] = new_log
        defaults["overwrite"] = new_over

        # Tool paths
        print(f"\nTool paths:")
        defaults["dataset_audit_path"] = ask("dataset_audit.py path", defaults.get("dataset_audit_path", DEFAULT_DATASET_AUDIT))
        defaults["propose_candidates_path"] = ask("propose_label_candidates.py path", defaults.get("propose_candidates_path", DEFAULT_PROPOSE_CANDS))
        defaults["spacy_trainer_path"] = ask("train_baseline_spacy.py path", defaults.get("spacy_trainer_path", DEFAULT_SPACY_TRAIN))
        defaults["backfill_lexicon_path"] = ask("backfill_strongs_lexicon.py path", defaults.get("backfill_lexicon_path", DEFAULT_BACKFILL_LEXICON))

        cfg["defaults"] = defaults
        save_yaml(CONFIG_FILE, cfg)
        print("Settings updated.")
        # Back to main automatically
        return cfg


def run_backfill_strongs():
    """Run the backfill_strongs_lexicon.py script against the DB."""
    db = DEFAULT_DB
    input_dir = ask("Path to STEP JSON root folder", "./STEP_JSON")
    cmd = [sys.executable, "./backfill_strongs_lexicon.py",
           "--db", db, "--input_dir", input_dir]
    try:
        stream_subprocess(cmd)
    except Exception as e:
        print(f"Error running backfill: {e}")

# ----------------------------
# Tools submenu
# ----------------------------
def tools_menu(cfg: Dict[str, Any]) -> None:
    """Run tools without typing args."""
    while True:
        print("\n=== Tools ===")
        print("[1] Audit current dataset (dataset_audit.py)")
        print("[2] Generate PERSON/PLACE candidate lists (propose_label_candidates.py)")
        print("[3] Train baseline spaCy model (train_baseline_spacy.py)")
        print("[4] Backfill Strong's lexicon (backfill_strongs_lexicon.py)")
        print("[B] Back to Main Menu")
        choice = input("Select: ").strip().lower()

        if choice in ("b", "back"):
            return

        if choice == "1":
            # Pick a profile to resolve outdir & rules paths (db not needed)
            name = select_profile_menu(cfg)
            if not name:
                continue
            resolved = resolve_profile(cfg, name)
            tool = resolved.get("dataset_audit_path", DEFAULT_DATASET_AUDIT)
            data_dir = resolved.get("outdir", DEFAULT_OUTDIR)
            if not os.path.exists(tool):
                print(f"Missing tool: {tool}")
                continue
            if not os.path.isdir(data_dir):
                print(f"Dataset directory not found: {data_dir}")
                continue
            cmd = [sys.executable, tool, "--data", data_dir, "--samples-per-label", "5"]
            print("\nRunning dataset audit:")
            print(" ".join(shlex.quote(c) for c in cmd))
            stream_subprocess(cmd)

        elif choice == "2":
            # Need DB path
            name = select_profile_menu(cfg)
            if not name:
                continue
            resolved = resolve_profile(cfg, name)
            tool = resolved.get("propose_candidates_path", DEFAULT_PROPOSE_CANDS)
            db = resolved.get("db", DEFAULT_DB)
            outdir = "./candidates"
            if not os.path.exists(tool):
                print(f"Missing tool: {tool}")
                continue
            if not os.path.exists(db):
                print(f"DB not found: {db}")
                continue
            os.makedirs(outdir, exist_ok=True)
            cmd = [sys.executable, tool, "--db", db, "--outdir", outdir]
            print("\nGenerating candidate lists:")
            print(" ".join(shlex.quote(c) for c in cmd))
            stream_subprocess(cmd)

        elif choice == "3":
            # Optional shortcut: train baseline spaCy on the current dataset directory
            name = select_profile_menu(cfg)
            if not name:
                continue
            resolved = resolve_profile(cfg, name)
            trainer = resolved.get("spacy_trainer_path", DEFAULT_SPACY_TRAIN)
            data_dir = resolved.get("outdir", DEFAULT_OUTDIR)
            out_model = os.path.join("./models", "spacy_silver_v1")
            os.makedirs("./models", exist_ok=True)
            if not os.path.exists(trainer):
                print(f"Missing trainer script: {trainer}")
                continue
            if not os.path.isdir(data_dir):
                print(f"Dataset directory not found: {data_dir}")
                continue
            cmd = [sys.executable, trainer, "--data", data_dir, "--output", out_model, "--epochs", "20"]
            print("\nTraining baseline spaCy model:")
            print(" ".join(shlex.quote(c) for c in cmd))
            stream_subprocess(cmd)

        elif choice == "4":
            # Backfill Strong's lexicon
            name = select_profile_menu(cfg)
            if not name:
                continue
            resolved = resolve_profile(cfg, name)
            tool = resolved.get("backfill_lexicon_path", DEFAULT_BACKFILL_LEXICON)
            db = resolved.get("db", DEFAULT_DB)
            if not os.path.exists(tool):
                print(f"Missing tool: {tool}")
                continue
            if not os.path.exists(db):
                print(f"DB not found: {db}")
                continue

            # Gather run-time options with sensible defaults
            step_dir = ask("STEP directory (where STEP_*.json exist)", ".")
            lex_json = ask("Optional master lexicon JSON (Enter to skip)", "")
            limit_str = ask("Optional limit files (int, Enter for all)", "")
            conflict_csv = ask("Optional conflicts CSV path (Enter to skip)", "")
            dry = yes_no("Dry run only?", False)

            cmd = [sys.executable, tool, "--db", db, "--step_dir", step_dir]
            if lex_json.strip():
                cmd += ["--lexicon_json", lex_json.strip()]
            if limit_str.strip():
                try:
                    int(limit_str.strip())
                    cmd += ["--limit_files", limit_str.strip()]
                except ValueError:
                    print("Ignoring invalid limit value.")
            if conflict_csv.strip():
                cmd += ["--conflict_csv", conflict_csv.strip()]
            if dry:
                cmd += ["--dry_run"]

            print("\nBackfilling Strong's lexicon:")
            print(" ".join(shlex.quote(c) for c in cmd))
            stream_subprocess(cmd)

        else:
            print("Invalid selection.")
            continue


# ----------------------------
# Main menu
# ----------------------------
def main_menu() -> None:
    cfg = ensure_config_exists()
    while True:
        print("\n=== Silver NER Export ===")
        print("[1] Run profile")
        print("[2] Pick a profile and customize")
        print("[3] Repeat last run")
        print("[4] Dry-run a profile (no files written)")
        print("[5] View label rules summary")
        print("[6] Batch run profiles")
        print("[7] Tools (audit, candidates, train, backfill)")
        print("[S] Settings")
        print("[Q] Quit")
        choice = input("Select: ").strip().lower()

        if choice in ("q", "quit"):
            print("Goodbye.")
            return

        if choice == "1":
            name = select_profile_menu(cfg)
            if not name:
                continue
            resolved = resolve_profile(cfg, name)
            run_export(resolved, name)

        elif choice == "2":
            name = select_profile_menu(cfg)
            if not name:
                continue
            resolved = resolve_profile(cfg, name)
            resolved2 = customize_profile_interactive(resolved)
            run_export(resolved2, name + "_custom")

        elif choice == "3":
            last = load_last_run()
            if not last:
                print("No last run cache found.")
                continue
            print(f"Repeating last run: profile={last['profile']}")
            run_export(last["resolved"], last["profile"])

        elif choice == "4":
            name = select_profile_menu(cfg)
            if not name:
                continue
            resolved = resolve_profile(cfg, name)
            resolved2 = dict(resolved)
            resolved2["dry_run"] = True
            dry_run_preview(resolved2["db"], resolved2["rules"], resolved2, resolved2.get("logging", "info"))

        elif choice == "5":
            # Use any profile's rules path (first one)
            first = next(iter(cfg.get("profiles", {})), None)
            if not first:
                print("No profiles defined.")
                continue
            res = resolve_profile(cfg, first)
            rules_path = res.get("rules", DEFAULT_RULES)
            print_rules_summary(rules_path)

        elif choice == "6":
            batch_run_menu(cfg)

        elif choice == "7":
            tools_menu(cfg)

        elif choice in ("s",):
            cfg = settings_menu(cfg)

        else:
            print("Invalid selection.")
            continue


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nInterrupted. Bye.")
