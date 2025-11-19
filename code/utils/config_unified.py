#!/usr/bin/env python3
"""
Unified Configuration Loader
Loads and provides access to the consolidated config.unified.yaml

Usage:
    from code.utils.config_unified import get_config, get_path

    # Load full config
    config = get_config()

    # Get specific values
    db_path = get_path('database', 'goodbook', 'path')
    log_level = get_config('logging', 'level')

    # Load with specific profile
    config = get_config(profile='gospels_holdout')
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
import os


class UnifiedConfig:
    """Unified configuration manager for Bible AI Database."""

    def __init__(self, config_path: Optional[str] = None, profile: Optional[str] = None):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to config.unified.yaml (default: project root)
            profile: Configuration profile to apply (default, gospels_holdout, ot_only)
        """
        if config_path is None:
            # Find config in project root (3 levels up from this file)
            config_path = Path(__file__).parent.parent.parent / 'config.yaml'

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.profile = profile

        if profile:
            self._apply_profile(profile)

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please ensure config.unified.yaml exists in the project root."
            )

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config

    def _apply_profile(self, profile: str):
        """Apply a configuration profile."""
        if 'profiles' not in self.config:
            raise ValueError("No profiles defined in configuration")

        if profile not in self.config['profiles']:
            available = list(self.config['profiles'].keys())
            raise ValueError(
                f"Profile '{profile}' not found. Available profiles: {available}"
            )

        profile_config = self.config['profiles'][profile]

        # Deep merge profile settings
        self._deep_update(self.config, profile_config)

    def _deep_update(self, base: Dict, update: Dict):
        """Deep merge update dict into base dict."""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get configuration value by nested keys.

        Args:
            *keys: Nested keys to navigate config
            default: Default value if key not found

        Returns:
            Configuration value

        Example:
            config.get('database', 'goodbook', 'path')
            config.get('logging', 'level', default='INFO')
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value

    def get_path(self, *keys: str, resolve: bool = True) -> Optional[Path]:
        """
        Get a path from configuration and optionally resolve it.

        Args:
            *keys: Nested keys to navigate config
            resolve: Whether to resolve relative paths to absolute

        Returns:
            Path object

        Example:
            db_path = config.get_path('database', 'goodbook', 'path')
        """
        path_str = self.get(*keys)
        if path_str is None:
            return None

        path = Path(path_str)

        if resolve and not path.is_absolute():
            # Resolve relative to project root
            project_root = self.config_path.parent
            path = project_root / path

        return path

    def get_database_path(self, db_name: str = 'goodbook') -> Path:
        """Get database path (convenience method)."""
        return self.get_path('database', db_name, 'path')

    def get_output_dir(self) -> Path:
        """Get output directory path (convenience method)."""
        return self.get_path('paths', 'output_dir')

    def get_log_dir(self) -> Path:
        """Get log directory path (convenience method)."""
        return self.get_path('paths', 'log_dir')

    def get_silver_export_config(self) -> Dict[str, Any]:
        """Get silver export configuration (convenience method)."""
        return self.get('silver_export', default={})

    def get_ai_training_config(self) -> Dict[str, Any]:
        """Get AI training configuration (convenience method)."""
        return self.get('ai_training', default={})

    def __getitem__(self, key: str) -> Any:
        """Allow dict-style access: config['database']"""
        return self.config[key]

    def __repr__(self) -> str:
        profile_str = f", profile='{self.profile}'" if self.profile else ""
        return f"UnifiedConfig(path='{self.config_path}'{profile_str})"


# Singleton instance for easy importing
_config_instance: Optional[UnifiedConfig] = None


def get_config(profile: Optional[str] = None, reload: bool = False) -> UnifiedConfig:
    """
    Get the global configuration instance.

    Args:
        profile: Configuration profile to apply
        reload: Force reload of configuration

    Returns:
        UnifiedConfig instance

    Example:
        config = get_config()
        config = get_config(profile='gospels_holdout')
    """
    global _config_instance

    if _config_instance is None or reload:
        _config_instance = UnifiedConfig(profile=profile)

    return _config_instance


def get_value(*keys: str, default: Any = None) -> Any:
    """
    Convenience function to get config value.

    Example:
        db_path = get_value('database', 'goodbook', 'path')
    """
    return get_config().get(*keys, default=default)


def get_path(*keys: str, resolve: bool = True) -> Optional[Path]:
    """
    Convenience function to get path from config.

    Example:
        log_dir = get_path('paths', 'log_dir')
    """
    return get_config().get_path(*keys, resolve=resolve)


if __name__ == "__main__":
    # Test configuration loading
    print("=" * 70)
    print("  Unified Configuration Test")
    print("=" * 70)
    print()

    try:
        # Load config
        config = get_config()
        print(f"✓ Configuration loaded: {config}")
        print()

        # Test value access
        print("Test value access:")
        print(f"  Project name: {config.get('project', 'name')}")
        print(f"  Project version: {config.get('project', 'version')}")
        print(f"  Database path: {config.get_database_path()}")
        print(f"  Log directory: {config.get_log_dir()}")
        print(f"  Bible version: {config.get('scraper', 'bible_version')}")
        print(f"  NLP model: {config.get('nlp', 'spacy_model')}")
        print()

        # Test profiles
        print("Test profiles:")
        for profile_name in ['default', 'gospels_holdout', 'ot_only']:
            prof_config = get_config(profile=profile_name, reload=True)
            holdout = prof_config.get('silver_export', 'holdout_books', default=[])
            print(f"  {profile_name}: holdout_books = {holdout}")
        print()

        print("✓ All tests passed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
