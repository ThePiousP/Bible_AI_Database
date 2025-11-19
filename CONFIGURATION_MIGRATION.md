# Configuration Migration Guide

**Date:** 2025-11-19
**Version:** 1.0.0

## Overview

The Bible AI Database project has consolidated **7 separate configuration files** into a single unified configuration system.

### Old Configuration Files (Deprecated)

| File | Purpose | Status |
|------|---------|--------|
| `config.yaml` | Main project config | ⚠️ **Replaced** by `config.unified.yaml` |
| `config.json` | Legacy config | ⚠️ **Deprecated** (use `config.unified.yaml`) |
| `step_config.json` | STEP Bible settings | ⚠️ **Consolidated** into `step:` section |
| `menu_master_CFG.json` | Menu settings | ⚠️ **Consolidated** into `menu:` section |
| `prodigy.json` | Prodigy keymaps | ⚠️ **Consolidated** into `prodigy:` section |
| `label_rules.yml` | Entity label rules | ✅ **Keep as-is** (domain content, not config) |
| `pytest.ini` | Test configuration | ✅ **Keep as-is** (test-specific) |

### New Unified Configuration

**File:** `config.unified.yaml`
**Python Loader:** `code/utils/config_unified.py`

## Migration Steps

### For Python Code

**Before (Old):**
```python
import json

with open('config.json', 'r') as f:
    config = json.load(f)

db_path = config['db_path']
```

**After (New):**
```python
from code.utils.config_unified import get_config, get_value, get_path

# Option 1: Get config instance
config = get_config()
db_path = config.get_database_path()

# Option 2: Direct value access
db_path = get_path('database', 'goodbook', 'path')
bible_version = get_value('scraper', 'bible_version')
```

### For Shell Scripts

**Before:**
```bash
# Read from multiple JSON files
DB_PATH=$(jq -r '.db_path' config.json)
BIBLE_VER=$(jq -r '.bible_version' config.json)
```

**After:**
```bash
# Use Python to read unified config
DB_PATH=$(python3 -c "from code.utils.config_unified import get_path; print(get_path('database', 'goodbook', 'path'))")
BIBLE_VER=$(python3 -c "from code.utils.config_unified import get_value; print(get_value('scraper', 'bible_version'))")
```

### Configuration Sections

The unified config is organized into these sections:

```yaml
# config.unified.yaml

project:           # Project metadata
paths:             # All file paths
database:          # Database configuration
scraper:           # Bible scraper settings
step:              # STEP Bible integration
menu:              # Interactive menu settings
nlp:               # NLP and NER configuration
silver_export:     # Silver dataset export
prodigy:           # Prodigy annotation tool
ai_training:       # AI training (NEW!)
logging:           # Logging configuration
advanced:          # Advanced/expert settings
profiles:          # Preset configurations
development:       # Development settings
deprecated:        # Backward compatibility
```

## Key Improvements

### 1. Single Source of Truth
- All configuration in one place
- No more hunting across 7 different files
- Easier to understand project settings

### 2. AI Training Configuration (New!)
```yaml
ai_training:
  embeddings:
    model_name: all-mpnet-base-v2
    batch_size: 32
  rag:
    top_k: 10
  chat:
    llm_provider: openai
    model: gpt-4
```

### 3. Profile Support
```python
# Load with specific profile
config = get_config(profile='gospels_holdout')

# Profiles: default, gospels_holdout, ot_only
```

### 4. Type-Safe Path Resolution
```python
# Automatically resolves relative paths
db_path = config.get_database_path()  # Returns absolute Path object
log_dir = config.get_log_dir()        # Creates dir if needed
```

### 5. Convenience Methods
```python
# Built-in helpers for common tasks
config.get_database_path('goodbook')
config.get_output_dir()
config.get_log_dir()
config.get_silver_export_config()
config.get_ai_training_config()
```

## Configuration Mapping

### Database Paths

**Old:**
- `config.json`: `db_path`
- `config.yaml`: `database.goodbook.path`
- `menu_master_CFG.json`: `database_path`

**New:**
```yaml
database:
  goodbook:
    path: data/GoodBook.db
```

### Bible Version

**Old:**
- `config.json`: `bible_version`
- `config.yaml`: `scraper.bible_version`
- `menu_master_CFG.json`: `bible_version`

**New:**
```yaml
scraper:
  bible_version: NKJV
```

### STEP Bible Settings

**Old:**
- `step_config.json`: All settings
- `menu_master_CFG.json`: `step_*` fields

**New:**
```yaml
step:
  parser_default: auto
  version_default: ESV
  options_default: NHVUG
  # ... all STEP settings consolidated
```

### Prodigy Keymaps

**Old:**
- `prodigy.json`: `keymap_by_label`

**New:**
```yaml
prodigy:
  keymap_by_label:
    DEITY: "d"
    PERSON: "p"
    LOCATION: "l"
    # ... all keymaps
```

## Backward Compatibility

The old configuration files remain in the repository for backward compatibility, but are marked as **deprecated**.

### Deprecation Timeline

- **2025-11-19:** `config.unified.yaml` introduced
- **2025-12-19:** Old configs marked deprecated (1 month grace period)
- **2026-01-19:** Old configs moved to `.archived/` (2 months)

### Migration Checklist

- [ ] Update code to use `code.utils.config_unified`
- [ ] Test with unified configuration
- [ ] Remove references to old config files
- [ ] Update documentation
- [ ] Update CI/CD pipelines

## Testing

Verify the unified configuration works:

```bash
# Test configuration loader
python3 code/utils/config_unified.py

# Test in your code
python3 -c "
from code.utils.config_unified import get_config
config = get_config()
print(f'DB Path: {config.get_database_path()}')
print(f'Version: {config.get(\"project\", \"version\")}')
"
```

## Support

If you encounter issues during migration:

1. Check `config.unified.yaml` for correct settings
2. Review `code/utils/config_unified.py` for API usage
3. Consult this migration guide
4. Open an issue on GitHub

## Example: Complete Migration

**Old Code:**
```python
import json
import yaml

# Load multiple configs
with open('config.json', 'r') as f:
    json_config = json.load(f)

with open('config.yaml', 'r') as f:
    yaml_config = yaml.safe_load(f)

with open('step_config.json', 'r') as f:
    step_config = json.load(f)

# Access values
db_path = json_config['db_path']
bible_version = json_config['bible_version']
output_dir = yaml_config['paths']['output_dir']
step_version = step_config['version_default']
```

**New Code:**
```python
from code.utils.config_unified import get_config

# Load once
config = get_config()

# Access all values
db_path = config.get_database_path()
bible_version = config.get('scraper', 'bible_version')
output_dir = config.get_output_dir()
step_version = config.get('step', 'version_default')

# Or use convenience functions
from code.utils.config_unified import get_value, get_path

db_path = get_path('database', 'goodbook', 'path')
bible_version = get_value('scraper', 'bible_version')
```

---

**Benefits:** Less code, type-safe, easier to maintain, single source of truth.
