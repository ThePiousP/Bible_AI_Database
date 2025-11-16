# Legacy Code Archive

**Date Archived:** 2025-10-30
**Reason:** Code refactoring and modernization (Phase 2)

---

## ⚠️ **Important Notice**

These files are **no longer actively maintained** and have been replaced by newer, refactored versions. They are kept here for:
- Historical reference
- Backup purposes
- Understanding the evolution of the codebase

**Do not use these files for new development.**

---

## 📦 **Legacy Files**

### **1. 66MASTER_v.983.py** (18KB)
**Status:** Obsolete
**Replaced by:** Modular architecture in `code/` directory
**Description:** Original monolithic master file from early development
**Last updated:** Pre-Phase 2

---

### **2. bible_scraper.py** (46KB)
**Status:** Replaced
**Replaced by:** `bible_scraper_OPTIMIZED.py`
**Description:** Original Bible scraper with cross-reference insertion
**Why replaced:** Performance issues (45-60 min vs. 3-5 min)
**Performance:** 15-20x slower than optimized version
**Last updated:** Before optimization work

---

### **3. entity_validator.py** (18KB)
**Status:** Legacy
**Description:** Entity validation utilities
**Note:** Validation logic may have been integrated into newer modules
**Last updated:** Phase 1

---

### **4. export_ner_silver.py** (36KB, 901 lines)
**Status:** Replaced
**Replaced by:** Modular silver export pipeline:
- `silver_data_models.py` - Data structures
- `silver_label_rules.py` - Label matching
- `silver_alignment.py` - Token alignment
- `silver_export.py` - Export orchestrator

**Description:** Original monolithic silver NER dataset exporter
**Why replaced:**
- Too large (901 lines)
- Mixed responsibilities
- No type hints
- Hard to test

**Last updated:** Before Phase 2 refactoring

---

### **5. menu_batch.py** (5KB)
**Status:** Obsolete
**Description:** Old batch menu system
**Note:** Menu functionality may have been moved to STEP/step_cli.py
**Last updated:** Pre-Phase 2

---

### **6. silver_menu.py** (28KB)
**Status:** Obsolete
**Description:** Old silver dataset menu interface
**Note:** Command-line interface superseded by direct script execution
**Last updated:** Phase 1

---

### **7. tag_strongs_entries.py** (7KB)
**Status:** Legacy
**Description:** Utility for tagging Strong's concordance entries
**Note:** Functionality may have been integrated into enrichment modules
**Last updated:** Early development

---

### **8. Tag Strongs to Json.py** (15KB)
**Status:** Legacy
**Description:** Strong's concordance to JSON converter
**Note:** File name contains spaces (non-standard)
**Last updated:** Early development

---

## 📊 **Statistics**

| Metric | Value |
|--------|-------|
| **Total files** | 8 |
| **Total size** | ~173 KB |
| **Lines of code** | ~2,500+ |
| **Archive date** | 2025-10-30 |

---

## 🔄 **Migration Path**

If you need functionality from these files:

### **For scraping/cross-references:**
Use `../bible_scraper_OPTIMIZED.py` instead of `bible_scraper.py`

### **For NER export:**
Use the modular silver export pipeline:
```python
from silver_data_models import Token, Verse, Span
from silver_label_rules import LabelRules
from silver_alignment import greedy_align_tokens_to_text, build_spans
from silver_export import export_silver_dataset
```

### **For Strong's tagging:**
Check `../STEP/step_enrichment.py` for modern implementation

---

## 🗑️ **Future Cleanup**

These files may be **permanently deleted** after:
- 6 months of no usage
- Verification that all functionality exists in new modules
- Project team approval

**Review date:** 2025-04-30

---

## 📞 **Questions?**

If you need to understand or reference legacy code, contact the project maintainer or check:
- `PHASE1_COMPLETE.md` - Phase 1 summary
- `PHASE2_COMPLETE.md` - Phase 2 refactoring details
- `PHASE2_EXPORT_NER_SPLIT.md` - Export module split documentation

---

**End of Legacy Code Archive README**

*Archived as part of Phase 3 cleanup - 2025-10-30*
