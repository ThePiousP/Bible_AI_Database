#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_config.py
Migration script: Old configs → New unified config.yaml

Migrates from:
  - config.json
  - project.yml
  - silver_config.yml

To:
  - config.yaml (unified)

Usage:
    python scripts/migrate_config.py
    python scripts/migrate_config.py --dry-run  # Preview changes
    python scripts/migrate_config.py --backup   # Create backup first

Created: 2025-10-29 (Phase 1 Refactoring)
"""

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    exit(1)


class ConfigMigrator:
    """Migrates old config files to new unified config.yaml"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_json = project_root / "config.json"
        self.project_yml = project_root / "project.yml"
        self.silver_config_yml = project_root / "silver_config.yml"
        self.config_yaml = project_root / "config.yaml"

    def check_old_configs(self) -> Dict[str, bool]:
        """Check which old config files exist"""
        return {
            'config.json': self.config_json.exists(),
            'project.yml': self.project_yml.exists(),
            'silver_config.yml': self.silver_config_yml.exists(),
        }

    def load_old_configs(self) -> Dict[str, Any]:
        """Load all old config files"""
        data = {}

        # Load config.json
        if self.config_json.exists():
            with open(self.config_json, 'r', encoding='utf-8') as f:
                data['config_json'] = json.load(f)

        # Load project.yml
        if self.project_yml.exists():
            with open(self.project_yml, 'r', encoding='utf-8') as f:
                data['project_yml'] = yaml.safe_load(f)

        # Load silver_config.yml
        if self.silver_config_yml.exists():
            with open(self.silver_config_yml, 'r', encoding='utf-8') as f:
                data['silver_config_yml'] = yaml.safe_load(f)

        return data

    def merge_configs(self, old_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge old configs into new unified format"""
        new_config = {
            'project': {
                'name': 'Bible NER Pipeline',
                'version': '0.983',
            },
            'paths': {},
            'database': {},
            'silver_export': {},
            'logging': {},
            'profiles': {},
        }

        # Migrate config.json
        if 'config_json' in old_data:
            cj = old_data['config_json']
            new_config['paths'] = {
                'data_dir': 'data',
                'cache_dir': cj.get('cache_dir', 'cache'),
                'output_dir': cj.get('output_dir', 'output/data'),
                'gazetteers_dir': 'gazetteers',
                'entity_dir': cj.get('entity_dir', 'bible_entities'),
                'log_dir': cj.get('logging_dir', 'output/LOGS'),
                'json_output_dir': cj.get('json_dir', 'output/json'),
                'cleaned_dir': cj.get('cleaned_dir', 'output/cleaned'),
                'html_cache_dir': cj.get('html_cache_dir', 'cache/html'),
            }

            new_config['database']['goodbook'] = {
                'path': cj.get('db_path', 'data/GoodBook.db'),
                'schema_version': 1,
                'expected_verses': 31102,
                'expected_books': 66,
            }

            new_config['scraper'] = {
                'bible_version': 'NKJV',
                'save_html_copy': cj.get('save_html_copy', True),
                'cache_enabled': True,
            }

            new_config['nlp'] = {
                'spacy_model': 'en_core_web_lg',
                'entity_ruler_config': cj.get('spacy_entity_ruler_config', {'overwrite_ents': False}),
            }

        # Migrate project.yml
        if 'project_yml' in old_data:
            py = old_data['project_yml']
            if 'defaults' in py:
                defaults = py['defaults']
                new_config['database']['concordance'] = {
                    'path': defaults.get('db_path', 'data/concordance.db'),
                    'schema_version': 1,
                    'expected_tokens': 400000,
                }

            # Migrate profiles
            if 'profiles' in py:
                new_config['profiles'] = py['profiles']

        # Migrate silver_config.yml
        if 'silver_config_yml' in old_data:
            sc = old_data['silver_config_yml']
            if 'defaults' in sc:
                defaults = sc['defaults']
                ratios = defaults.get('ratios', [0.8, 0.1, 0.1])
                new_config['silver_export'] = {
                    'text_prefer': defaults.get('text_prefer', 'auto'),
                    'seed': defaults.get('seed', 13),
                    'ratios': {
                        'train': ratios[0],
                        'dev': ratios[1],
                        'test': ratios[2],
                    },
                    'holdout_books': defaults.get('holdout_books', []),
                    'holdout_name': defaults.get('holdout_name', 'domain_holdout'),
                    'require_clean': False,
                    'align_report': False,
                    'label_on_miss': defaults.get('label_on_miss'),
                    'output_dir': defaults.get('outdir', 'output/silver_out'),
                }

            # Migrate profiles from silver_config
            if 'profiles' in sc:
                for profile_name, profile_data in sc['profiles'].items():
                    if profile_name not in new_config['profiles']:
                        new_config['profiles'][profile_name] = {}
                    new_config['profiles'][profile_name]['silver_export'] = profile_data

        # Add logging defaults
        new_config['logging'] = {
            'level': 'INFO',
            'format': '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'file_logging': {
                'enabled': True,
                'directory': 'output/LOGS',
                'max_bytes': 10485760,
                'backup_count': 5,
            },
            'console': {
                'enabled': True,
                'colored': True,
            }
        }

        # Add labels configuration
        new_config['labels'] = {
            'rules_file': 'label_rules.yml',
            'num_labels': 65,
            'gazetteers_required': True,
        }

        # Add advanced settings
        new_config['advanced'] = {
            'alignment': {
                'fallback_window': 200,
                'whitespace_tolerance': True,
            },
            'strongs': {
                'hebrew_range': [1, 8674],
                'greek_range': [1, 5624],
            },
            'performance': {
                'batch_size': 5000,
                'cache_verse_lookups': True,
            },
        }

        return new_config

    def backup_old_configs(self):
        """Create backup of old config files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.project_root / f"Folders/REFACTOR_BACKUPS/config_backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        backed_up = []
        for config_file in [self.config_json, self.project_yml, self.silver_config_yml]:
            if config_file.exists():
                backup_path = backup_dir / config_file.name
                shutil.copy2(config_file, backup_path)
                backed_up.append(config_file.name)

        return backup_dir, backed_up

    def rename_old_configs(self):
        """Rename old configs to .old extension"""
        renamed = []
        for config_file in [self.config_json, self.project_yml, self.silver_config_yml]:
            if config_file.exists():
                old_path = config_file.with_suffix(config_file.suffix + '.old')
                config_file.rename(old_path)
                renamed.append((config_file.name, old_path.name))
        return renamed

    def write_new_config(self, config_data: Dict[str, Any]):
        """Write new config.yaml"""
        with open(self.config_yaml, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def migrate(self, dry_run: bool = False, backup: bool = True):
        """Run full migration"""
        print("=" * 70)
        print("Bible NER Pipeline - Config Migration")
        print("=" * 70)
        print()

        # Check what we're migrating
        old_configs = self.check_old_configs()
        print("Old config files found:")
        for name, exists in old_configs.items():
            status = "✓" if exists else "✗"
            print(f"  {status} {name}")
        print()

        if not any(old_configs.values()):
            print("No old config files found. Nothing to migrate.")
            return

        if self.config_yaml.exists():
            print(f"⚠️  WARNING: {self.config_yaml.name} already exists!")
            response = input("Overwrite? (yes/no): ")
            if response.lower() != 'yes':
                print("Migration cancelled.")
                return
            print()

        # Load old configs
        print("Loading old config files...")
        old_data = self.load_old_configs()
        print("✓ Loaded successfully")
        print()

        # Merge into new format
        print("Merging configurations...")
        new_config = self.merge_configs(old_data)
        print("✓ Merged successfully")
        print()

        if dry_run:
            print("DRY RUN - Preview of new config.yaml:")
            print("-" * 70)
            print(yaml.dump(new_config, default_flow_style=False, sort_keys=False))
            print("-" * 70)
            print("\nNo files were modified (dry run mode)")
            return

        # Backup old configs
        if backup:
            print("Creating backup...")
            backup_dir, backed_up = self.backup_old_configs()
            print(f"✓ Backed up to: {backup_dir}")
            for filename in backed_up:
                print(f"    - {filename}")
            print()

        # Write new config
        print("Writing new config.yaml...")
        self.write_new_config(new_config)
        print(f"✓ Created: {self.config_yaml}")
        print()

        # Rename old configs
        print("Renaming old config files...")
        renamed = self.rename_old_configs()
        for old_name, new_name in renamed:
            print(f"  {old_name} → {new_name}")
        print()

        print("=" * 70)
        print("✅ Migration completed successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Review new config.yaml")
        print("  2. Test with: python code/utils/config_loader.py")
        print("  3. Update your scripts to use new config")
        print("  4. Old configs (.old files) can be deleted after testing")
        print()


def main():
    parser = argparse.ArgumentParser(description='Migrate old config files to unified config.yaml')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying files')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup')
    parser.add_argument('--project-root', type=str, help='Project root directory (auto-detected if not specified)')

    args = parser.parse_args()

    # Detect project root
    if args.project_root:
        project_root = Path(args.project_root)
    else:
        # Assume script is in scripts/ subdirectory
        project_root = Path(__file__).parent.parent

    # Run migration
    migrator = ConfigMigrator(project_root)
    migrator.migrate(dry_run=args.dry_run, backup=not args.no_backup)


if __name__ == '__main__':
    main()
