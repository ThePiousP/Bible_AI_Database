#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_loader.py
Unified configuration loader with backward compatibility

BEFORE (loading configs manually):
  - json.load(open("config.json"))
  - yaml.safe_load(open("project.yml"))
  - Settings scattered, no validation

AFTER (centralized loading):
  - Load from config.yaml (preferred)
  - Fallback to old config files (with warnings)
  - Pydantic validation
  - Environment variable overrides
  - Profile support

Created: 2025-10-29 (Phase 1 Refactoring)

Usage:
    from code.utils.config_loader import load_config

    config = load_config()
    db_path = config.database.concordance.path
    log_level = config.logging.level
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, List
import warnings

try:
    import yaml
except ImportError:
    yaml = None

try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    # Pydantic is optional (graceful degradation)
    BaseModel = object
    Field = lambda *args, **kwargs: None

    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


# ============================================================================
# Configuration Models (Pydantic)
# ============================================================================

class DatabaseConfig(BaseModel):
    """Database connection settings"""
    path: str
    schema_version: int = 1
    expected_verses: Optional[int] = None
    expected_books: Optional[int] = None
    expected_tokens: Optional[int] = None


class PathsConfig(BaseModel):
    """Path configuration"""
    data_dir: str = "data"
    cache_dir: str = "cache"
    output_dir: str = "output"
    gazetteers_dir: str = "gazetteers"
    entity_dir: str = "bible_entities"
    log_dir: str = "output/LOGS"


class SilverExportConfig(BaseModel):
    """Silver dataset export settings"""
    text_prefer: str = "auto"
    seed: int = 13
    ratios: Dict[str, float] = {"train": 0.8, "dev": 0.1, "test": 0.1}
    holdout_books: List[str] = []
    holdout_name: str = "domain_holdout"
    require_clean: bool = False
    align_report: bool = False
    label_on_miss: Optional[str] = None
    output_dir: str = "output/silver_out"

    @validator('ratios')
    def validate_ratios(cls, v):
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):  # Allow small float errors
            raise ValueError(f"Ratios must sum to 1.0, got {total}")
        return v


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class Config(BaseModel):
    """Root configuration object"""
    project: Optional[Dict[str, Any]] = None
    paths: Optional[PathsConfig] = None
    database: Optional[Dict[str, DatabaseConfig]] = None
    silver_export: Optional[SilverExportConfig] = None
    logging: Optional[LoggingConfig] = None
    profiles: Optional[Dict[str, Any]] = None
    advanced: Optional[Dict[str, Any]] = None

    class Config:
        # Allow extra fields for future compatibility
        extra = "allow"


# ============================================================================
# Configuration Loader
# ============================================================================

class ConfigLoader:
    """
    Loads configuration with backward compatibility.

    Priority:
      1. config.yaml (new unified config)
      2. config.json + project.yml + silver_config.yml (old configs)
      3. Default values
    """

    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Auto-detect project root (go up from code/utils/)
            self.project_root = Path(__file__).parent.parent.parent.resolve()
        else:
            self.project_root = Path(project_root).resolve()

        self.config_yaml = self.project_root / "config.yaml"
        self.config_json = self.project_root / "config.json"
        self.project_yml = self.project_root / "project.yml"
        self.silver_config_yml = self.project_root / "silver_config.yml"

    def load(self, profile: Optional[str] = None) -> Config:
        """
        Load configuration.

        Args:
            profile: Optional profile name (e.g., "gospels_holdout")

        Returns:
            Validated Config object
        """
        # Try new unified config first
        if self.config_yaml.exists():
            return self._load_new_config(profile)

        # Fall back to old configs (with warning)
        warnings.warn(
            "Using legacy config files (config.json, project.yml). "
            "Run 'python scripts/migrate_config.py' to upgrade to unified config.yaml",
            DeprecationWarning
        )
        return self._load_legacy_config()

    def _load_new_config(self, profile: Optional[str]) -> Config:
        """Load from unified config.yaml"""
        if yaml is None:
            raise ImportError("PyYAML is required. Install with: pip install pyyaml")

        with open(self.config_yaml, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Apply profile overrides if specified
        if profile and 'profiles' in data and profile in data['profiles']:
            profile_data = data['profiles'][profile]
            data = self._merge_dicts(data, profile_data)

        # Apply environment variable overrides
        data = self._apply_env_overrides(data)

        # Validate with Pydantic (if available)
        if BaseModel != object:
            return Config(**data)
        else:
            # Return as dict-like object if Pydantic not available
            return type('Config', (), data)

    def _load_legacy_config(self) -> Config:
        """Load from old config files"""
        data = {}

        # Load config.json
        if self.config_json.exists():
            with open(self.config_json, 'r', encoding='utf-8') as f:
                config_json = json.load(f)
                data.update({
                    'paths': {
                        'data_dir': 'data',
                        'output_dir': config_json.get('output_dir', 'output/data'),
                        'log_dir': config_json.get('logging_dir', 'output/LOGS'),
                        'cache_dir': config_json.get('cache_dir', 'cache'),
                        'entity_dir': config_json.get('entity_dir', 'bible_entities'),
                    },
                    'database': {
                        'goodbook': {
                            'path': config_json.get('db_path', 'data/GoodBook.db'),
                            'schema_version': 1
                        }
                    }
                })

        # Load project.yml
        if yaml and self.project_yml.exists():
            with open(self.project_yml, 'r', encoding='utf-8') as f:
                project_yml = yaml.safe_load(f)
                if 'defaults' in project_yml:
                    defaults = project_yml['defaults']
                    data['database'] = data.get('database', {})
                    data['database']['concordance'] = {
                        'path': defaults.get('db_path', 'data/concordance.db'),
                        'schema_version': 1
                    }

        # Load silver_config.yml
        if yaml and self.silver_config_yml.exists():
            with open(self.silver_config_yml, 'r', encoding='utf-8') as f:
                silver_config = yaml.safe_load(f)
                if 'defaults' in silver_config:
                    defaults = silver_config['defaults']
                    data['silver_export'] = {
                        'seed': defaults.get('seed', 13),
                        'ratios': {
                            'train': defaults.get('ratios', [0.8, 0.1, 0.1])[0],
                            'dev': defaults.get('ratios', [0.8, 0.1, 0.1])[1],
                            'test': defaults.get('ratios', [0.8, 0.1, 0.1])[2],
                        },
                        'output_dir': defaults.get('outdir', 'output/silver_out'),
                        'text_prefer': defaults.get('text_prefer', 'auto'),
                    }

        # Convert to Config object
        if BaseModel != object:
            return Config(**data)
        else:
            return type('Config', (), data)

    def _merge_dicts(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value
        return result

    def _apply_env_overrides(self, data: Dict) -> Dict:
        """Apply environment variable overrides"""
        # Example: BIBLE_DATABASE_CONCORDANCE_PATH overrides database.concordance.path

        env_mappings = {
            'BIBLE_DATA_DIR': ('paths', 'data_dir'),
            'BIBLE_CONCORDANCE_DB': ('database', 'concordance', 'path'),
            'BIBLE_GOODBOOK_DB': ('database', 'goodbook', 'path'),
            'BIBLE_LOG_LEVEL': ('logging', 'level'),
            'BIBLE_OUTPUT_DIR': ('paths', 'output_dir'),
        }

        for env_var, path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Navigate to the nested key and set value
                current = data
                for key in path[:-1]:
                    current = current.setdefault(key, {})
                current[path[-1]] = value

        return data


# ============================================================================
# Convenience Functions
# ============================================================================

def load_config(profile: Optional[str] = None, project_root: Optional[Path] = None) -> Config:
    """
    Load configuration (convenience function).

    Example:
        from code.utils.config_loader import load_config

        config = load_config()
        db_path = config.database['concordance'].path

        # With profile:
        config = load_config(profile='gospels_holdout')
    """
    loader = ConfigLoader(project_root=project_root)
    return loader.load(profile=profile)


def get_config_summary(config: Config) -> str:
    """Get human-readable summary of configuration"""
    lines = [
        "Configuration Summary",
        "=" * 60,
    ]

    if hasattr(config, 'project') and config.project:
        lines.append(f"Project: {config.project.get('name', 'Unknown')} v{config.project.get('version', '?')}")
        lines.append("")

    if hasattr(config, 'database') and config.database:
        lines.append("Databases:")
        for db_name, db_config in config.database.items():
            path = db_config.path if hasattr(db_config, 'path') else db_config.get('path', '?')
            lines.append(f"  {db_name}: {path}")
        lines.append("")

    if hasattr(config, 'silver_export') and config.silver_export:
        se = config.silver_export
        lines.append("Silver Export:")
        lines.append(f"  Seed: {se.seed}")
        lines.append(f"  Ratios: train={se.ratios['train']}, dev={se.ratios['dev']}, test={se.ratios['test']}")
        if se.holdout_books:
            lines.append(f"  Holdout: {', '.join(se.holdout_books)}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    # Example 1: Load default config
    print("Loading configuration...")
    config = load_config()

    # Print summary
    print(get_config_summary(config))

    # Example 2: Access settings
    if hasattr(config, 'database') and config.database:
        print("\nDatabase paths:")
        for db_name, db_config in config.database.items():
            path = db_config.path if hasattr(db_config, 'path') else db_config.get('path', '?')
            print(f"  {db_name}: {path}")

    # Example 3: Load with profile
    print("\n" + "=" * 60)
    print("Loading with 'gospels_holdout' profile...")
    try:
        config_holdout = load_config(profile='gospels_holdout')
        if hasattr(config_holdout, 'silver_export'):
            se = config_holdout.silver_export
            print(f"  Holdout books: {se.holdout_books}")
            print(f"  Output dir: {se.output_dir}")
    except Exception as e:
        print(f"  (Profile not available: {e})")

    # Example 4: Environment variable override
    print("\n" + "=" * 60)
    print("Environment variable support:")
    print("  Set BIBLE_DATA_DIR to override data directory")
    print("  Set BIBLE_CONCORDANCE_DB to override concordance.db path")
    print("  Set BIBLE_LOG_LEVEL to override log level")

    # Test
    test_env = os.getenv("BIBLE_DATA_DIR")
    if test_env:
        print(f"\n  ✓ BIBLE_DATA_DIR is set: {test_env}")
    else:
        print(f"\n  (Set BIBLE_DATA_DIR=/custom/path to test override)")

    print("\n✓ Configuration loading successful!")
