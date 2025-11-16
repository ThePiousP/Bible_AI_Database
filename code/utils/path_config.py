#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
path_config.py
Centralized path configuration with environment variable support

BEFORE (scattered hardcoded paths):
  - export_ner_silver.py:643 → "C:\\BIBLE\\concordance.db"
  - CMDs.txt → "C:\\BIBLE\\concordance.db"
  - config.json → "GoodBook.db" (relative, no validation)

AFTER (centralized with fallbacks):
  - Environment variable: BIBLE_DATA_DIR (optional override)
  - Fallback to relative paths from project root
  - Validation of paths before use
  - Cross-platform path handling (Windows/Linux/Mac)

Created: 2025-10-29 (Phase 1 Refactoring)
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, Union
import json


class PathConfig:
    """
    Centralized path configuration for the Bible NER pipeline.

    Priority for resolving paths:
      1. Environment variables (BIBLE_DATA_DIR, BIBLE_CONCORDANCE_DB, etc.)
      2. Config file settings (config.json or unified config.yaml)
      3. Default relative paths from project root

    Example usage:
        paths = PathConfig()
        db_path = paths.concordance_db  # Gets path with fallbacks
        paths.ensure_dirs()  # Creates necessary directories

    Migration from old code:
        # OLD:
        db_path = "C:\\BIBLE\\concordance.db"  # Hardcoded

        # NEW:
        from code.utils.path_config import PathConfig
        paths = PathConfig()
        db_path = paths.concordance_db  # Portable, validated
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None, project_root: Optional[Path] = None):
        """
        Initialize path configuration.

        Args:
            config_path: Path to config.json (optional, auto-detected if None)
            project_root: Project root directory (auto-detected if None)
        """
        # Detect project root (go up from code/utils/ to project root)
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent.resolve()
        else:
            self.project_root = Path(project_root).resolve()

        # Load configuration file (if exists)
        self.config: Dict[str, Any] = {}
        if config_path is None:
            # Auto-detect config.json in project root
            config_path = self.project_root / "config.json"

        if Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # Don't fail if config is invalid, just use defaults
                print(f"Warning: Could not load config from {config_path}: {e}")

    # ========================================================================
    # Core Directories
    # ========================================================================

    @property
    def data_dir(self) -> Path:
        """
        Data directory (contains databases).

        Priority:
          1. Environment variable: BIBLE_DATA_DIR
          2. Config file: data_dir or db_path (directory part)
          3. Default: {project_root}/data
        """
        # Check environment variable first
        env_path = os.getenv("BIBLE_DATA_DIR")
        if env_path:
            return Path(env_path).resolve()

        # Check config file
        config_path = self.config.get("data_dir") or self.config.get("db_path")
        if config_path:
            path = Path(config_path)
            # If it's a file path, get the directory
            if path.suffix:  # Has file extension
                return path.parent.resolve()
            return path.resolve()

        # Default: relative to project root
        return self.project_root / "data"

    @property
    def cache_dir(self) -> Path:
        """Cache directory (HTML, STEP, Strong's data)."""
        return self._get_dir("cache_dir", self.project_root / "cache")

    @property
    def output_dir(self) -> Path:
        """Output directory (generated files, logs)."""
        return self._get_dir("output_dir", self.project_root / "output")

    @property
    def gazetteers_dir(self) -> Path:
        """Gazetteers directory (entity lists)."""
        return self._get_dir("gazetteers_dir", self.project_root / "gazetteers")

    @property
    def entity_dir(self) -> Path:
        """Entity reference files directory."""
        return self._get_dir("entity_dir", self.project_root / "bible_entities")

    @property
    def log_dir(self) -> Path:
        """Log directory."""
        log_path = self._get_dir("logging_dir", self.output_dir / "LOGS")
        # Ensure it exists
        log_path.mkdir(parents=True, exist_ok=True)
        return log_path

    # ========================================================================
    # Database Paths
    # ========================================================================

    @property
    def goodbook_db(self) -> Path:
        """
        Path to GoodBook.db.

        Priority:
          1. Environment variable: BIBLE_GOODBOOK_DB
          2. Config file: goodbook_db or db_path
          3. Default: {data_dir}/GoodBook.db
        """
        env_path = os.getenv("BIBLE_GOODBOOK_DB")
        if env_path:
            return Path(env_path).resolve()

        config_path = self.config.get("goodbook_db") or self.config.get("db_path")
        if config_path:
            path = Path(config_path)
            if path.name == "GoodBook.db" or "goodbook" in path.name.lower():
                return path.resolve() if path.is_absolute() else (self.project_root / path).resolve()

        return self.data_dir / "GoodBook.db"

    @property
    def concordance_db(self) -> Path:
        """
        Path to concordance.db.

        Priority:
          1. Environment variable: BIBLE_CONCORDANCE_DB
          2. Config file: concordance_db
          3. Default: {data_dir}/concordance.db

        BEFORE: Hardcoded "C:\\BIBLE\\concordance.db" in export_ner_silver.py
        AFTER: Portable path with environment variable override
        """
        env_path = os.getenv("BIBLE_CONCORDANCE_DB")
        if env_path:
            return Path(env_path).resolve()

        config_path = self.config.get("concordance_db")
        if config_path:
            path = Path(config_path)
            return path.resolve() if path.is_absolute() else (self.project_root / path).resolve()

        return self.data_dir / "concordance.db"

    @property
    def prodigy_db(self) -> Path:
        """Path to prodigy.db (annotation database)."""
        return self.project_root / "prodigy.db"

    # ========================================================================
    # Configuration Files
    # ========================================================================

    @property
    def label_rules_yml(self) -> Path:
        """Path to label_rules.yml."""
        return self.project_root / "label_rules.yml"

    @property
    def config_json(self) -> Path:
        """Path to config.json (legacy)."""
        return self.project_root / "config.json"

    @property
    def config_yaml(self) -> Path:
        """Path to unified config.yaml (new)."""
        return self.project_root / "config.yaml"

    # ========================================================================
    # Output Paths
    # ========================================================================

    @property
    def silver_out_dir(self) -> Path:
        """Silver dataset output directory."""
        return self.output_dir / "silver_out"

    @property
    def json_output_dir(self) -> Path:
        """JSON output directory (STEP exports)."""
        return self._get_dir("json_dir", self.output_dir / "json")

    @property
    def cleaned_dir(self) -> Path:
        """Cleaned text output directory."""
        return self._get_dir("cleaned_dir", self.output_dir / "cleaned")

    # ========================================================================
    # Cache Subdirectories
    # ========================================================================

    @property
    def html_cache_dir(self) -> Path:
        """HTML cache directory (BibleGateway)."""
        return self._get_dir("html_cache_dir", self.cache_dir / "html")

    @property
    def strongs_cache_dir(self) -> Path:
        """Strong's data cache directory."""
        return self.cache_dir / "STRONGS"

    @property
    def step_cache_dir(self) -> Path:
        """STEP data cache directory."""
        return self.cache_dir / "STEP"

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _get_dir(self, config_key: str, default: Path) -> Path:
        """Get directory path from config or use default."""
        config_path = self.config.get(config_key)
        if config_path:
            path = Path(config_path)
            return path.resolve() if path.is_absolute() else (self.project_root / path).resolve()
        return default

    def ensure_dirs(self) -> None:
        """Create all necessary directories if they don't exist."""
        dirs_to_create = [
            self.data_dir,
            self.cache_dir,
            self.output_dir,
            self.log_dir,
            self.silver_out_dir,
            self.json_output_dir,
            self.cleaned_dir,
            self.html_cache_dir,
            self.strongs_cache_dir,
            self.step_cache_dir,
        ]

        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)

    def validate_databases(self) -> Dict[str, bool]:
        """
        Check which databases exist.

        Returns:
            Dictionary mapping database names to existence status
        """
        return {
            "GoodBook.db": self.goodbook_db.exists(),
            "concordance.db": self.concordance_db.exists(),
            "prodigy.db": self.prodigy_db.exists(),
        }

    def get_summary(self) -> str:
        """Get human-readable summary of path configuration."""
        lines = [
            "Bible NER Pipeline - Path Configuration",
            "=" * 60,
            f"Project Root: {self.project_root}",
            "",
            "Directories:",
            f"  Data:        {self.data_dir}",
            f"  Cache:       {self.cache_dir}",
            f"  Output:      {self.output_dir}",
            f"  Gazetteers:  {self.gazetteers_dir}",
            f"  Entities:    {self.entity_dir}",
            f"  Logs:        {self.log_dir}",
            "",
            "Databases:",
            f"  GoodBook:    {self.goodbook_db} {'✓' if self.goodbook_db.exists() else '✗'}",
            f"  Concordance: {self.concordance_db} {'✓' if self.concordance_db.exists() else '✗'}",
            f"  Prodigy:     {self.prodigy_db} {'✓' if self.prodigy_db.exists() else '✗'}",
            "",
            "Configuration:",
            f"  Config file: {self.config_json if self.config_json.exists() else 'Not found'}",
            f"  Label rules: {self.label_rules_yml if self.label_rules_yml.exists() else 'Not found'}",
            "=" * 60,
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"PathConfig(project_root={self.project_root})"


# ============================================================================
# Convenience Functions
# ============================================================================

def get_paths(config_path: Optional[str] = None) -> PathConfig:
    """
    Get PathConfig instance (singleton-like usage).

    This is the recommended way to get paths in your scripts:

    Example:
        from code.utils.path_config import get_paths

        paths = get_paths()
        db_path = paths.concordance_db
    """
    return PathConfig(config_path=config_path)


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    # Example usage and validation
    paths = PathConfig()

    print(paths.get_summary())

    # Test environment variable override
    print("\nEnvironment variable support:")
    print(f"  Set BIBLE_DATA_DIR to override data directory")
    print(f"  Set BIBLE_CONCORDANCE_DB to override concordance.db path")

    # Ensure directories exist
    print("\nCreating directories...")
    paths.ensure_dirs()
    print("✓ All directories created/verified")

    # Validate databases
    print("\nDatabase validation:")
    db_status = paths.validate_databases()
    for db_name, exists in db_status.items():
        status = "✓ EXISTS" if exists else "✗ NOT FOUND"
        print(f"  {db_name}: {status}")
