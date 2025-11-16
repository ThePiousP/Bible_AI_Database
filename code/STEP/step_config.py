# step_config.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import json

CONFIG_PATH = Path("step_config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "parser_default": "auto",            # auto | selectolax | bs4
    "include_italics_default": True,     # <- italics default lives here
    "version_default": "KJV",
    "options_default": "NHVUG",
    "output_dir": "output/json",         # one JSON per chapter
    "log_dir": "output/logs",
    "html_cache_dir": "cache/html",      # cached HTML files from STEP server
    "continue_on_error": True,
    "batch_defaults": {"start_chapter": 1, "end_chapter": 50}
}

def _ensure_dirs(cfg: Dict[str, Any]) -> None:
    Path(cfg.get("output_dir", "output/json")).mkdir(parents=True, exist_ok=True)
    Path(cfg.get("log_dir", "output/logs")).mkdir(parents=True, exist_ok=True)
    Path(cfg.get("html_cache_dir", "cache/html")).mkdir(parents=True, exist_ok=True)

def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG.copy())
        return DEFAULT_CONFIG.copy()
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        merged = DEFAULT_CONFIG.copy()
        merged.update(cfg or {})
        bd = DEFAULT_CONFIG["batch_defaults"].copy()
        bd.update((cfg.get("batch_defaults") or {}))
        merged["batch_defaults"] = bd
        _ensure_dirs(merged)
        return merged
    except Exception:
        save_config(DEFAULT_CONFIG.copy())
        return DEFAULT_CONFIG.copy()

def save_config(cfg: Dict[str, Any]) -> None:
    _ensure_dirs(cfg)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def set_field(key: str, value: Any) -> Dict[str, Any]:
    cfg = load_config()
    if key == "batch_defaults" and isinstance(value, dict):
        bd = cfg.get("batch_defaults", {}).copy()
        bd.update(value)
        cfg["batch_defaults"] = bd
    else:
        cfg[key] = value
    save_config(cfg)
    return cfg