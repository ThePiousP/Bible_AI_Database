# Test Suite for Bible NER Pipeline

Comprehensive pytest test suite for the Bible NER Pipeline.

## 📊 Test Coverage

| Module | Tests | Coverage Target |
|--------|-------|----------------|
| `silver_alignment.py` | 12 tests | >95% |
| `silver_label_rules.py` | 14 tests | >90% |
| `step_morph_parser.py` | 13 tests | >85% |
| **TOTAL** | **39 tests** | **>80%** |

## 🚀 Quick Start

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
# or
run_pytest.bat
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest -m unit

# Alignment tests
pytest -m alignment

# Label rules tests
pytest -m labels

# Parsing tests
pytest -m parsing
```

### Run with Coverage

```bash
pytest --cov=code --cov-report=html
# Open htmlcov/index.html to view report
```

## 📁 Test Structure

```
tests/
├── __init__.py                 # Test package init
├── conftest.py                 # Shared fixtures
├── test_alignment.py           # Alignment algorithm tests (12 tests)
├── test_label_rules.py         # Label matching tests (14 tests)
├── test_step_parser.py         # STEP parsing tests (13 tests)
└── fixtures/                   # Test data (optional)
```

## 🏷️ Test Markers

Tests are organized using pytest markers:

| Marker | Description | Count |
|--------|-------------|-------|
| `@pytest.mark.unit` | Fast, isolated unit tests | 35+ |
| `@pytest.mark.integration` | Integration tests (slower) | 4 |
| `@pytest.mark.slow` | Slow tests (>1 second) | TBD |
| `@pytest.mark.alignment` | Alignment algorithm tests | 12 |
| `@pytest.mark.labels` | Label matching tests | 14 |
| `@pytest.mark.parsing` | Parsing tests | 13 |

### Running Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only alignment tests
pytest -m alignment

# Run all except slow tests
pytest -m "not slow"
```

## 📝 Test Files

### test_alignment.py (12 tests)

Tests for greedy text alignment algorithm:

- ✅ `test_perfect_alignment` - All tokens align correctly
- ✅ `test_alignment_with_missing_token` - Handle missing tokens
- ✅ `test_alignment_with_whitespace_variations` - Handle extra spaces
- ✅ `test_alignment_preserves_order` - Left-to-right ordering
- ✅ `test_empty_token_alignment` - Handle empty tokens
- ✅ `test_build_spans_basic` - Build labeled spans
- ✅ `test_build_spans_with_merging` - Merge contiguous spans
- ✅ `test_build_spans_with_phrases` - Phrase matching
- ✅ `test_calculate_alignment_stats` - Statistics calculation
- ✅ `test_calculate_alignment_stats_empty` - Empty list handling
- ✅ `test_alignment_with_repeated_words` - Repeated tokens
- ✅ `test_alignment_with_special_characters` - Punctuation handling

### test_label_rules.py (14 tests)

Tests for label matching and priority resolution:

- ✅ `test_strongs_id_matching` - Match by Hebrew Strong's ID
- ✅ `test_strongs_id_matching_greek` - Match by Greek Strong's ID
- ✅ `test_no_strongs_id` - Handle missing Strong's ID
- ✅ `test_lemma_matching` - Match by Hebrew lemma
- ✅ `test_lemma_matching_greek` - Match by Greek lemma
- ✅ `test_surface_matching` - Match by surface form
- ✅ `test_surface_matching_case_sensitive` - Case sensitivity
- ✅ `test_surface_matching_case_insensitive` - Case insensitivity
- ✅ `test_priority_resolution` - Conflict resolution
- ✅ `test_priority_resolution_reversed` - Reversed priority
- ✅ `test_phrase_matching_basic` - Multi-word phrases
- ✅ `test_phrase_matching_partial_match` - Partial phrase matching
- ✅ `test_phrase_override_mask` - Phrase override labels
- ✅ `test_phrase_matching_case_sensitive` - Case-sensitive phrases
- ✅ `test_gazetteer_loading_txt` - Load gazetteers from TXT
- ✅ `test_gazetteer_missing_file` - Handle missing gazetteer
- ✅ `test_empty_token_surface` - Empty surface handling
- ✅ `test_label_on_miss` - Default labels
- ✅ `test_multiple_strongs_ids` - Multiple Strong's IDs

### test_step_parser.py (13 tests)

Tests for STEP XML and morphology parsing:

- ✅ `test_parse_hebrew_morph_noun` - Parse Hebrew noun morph
- ✅ `test_parse_hebrew_morph_verb` - Parse Hebrew verb morph
- ✅ `test_parse_hebrew_morph_article` - Parse Hebrew article
- ✅ `test_parse_greek_morph_verb` - Parse Greek verb morph
- ✅ `test_parse_greek_morph_noun` - Parse Greek noun morph
- ✅ `test_parse_greek_morph_preposition` - Parse Greek preposition
- ✅ `test_parse_invalid_morph_code` - Handle invalid codes
- ✅ `test_parse_empty_morph_code` - Handle empty codes
- ✅ `test_parse_morph_unknown_language` - Handle unknown language
- ✅ `test_clean_text_basic` - Basic text cleaning
- ✅ `test_normalize_whitespace` - Whitespace normalization
- ✅ `test_strip_hebrew_vowels` - Hebrew vowel removal
- ✅ `test_clean_text_with_punctuation` - Preserve punctuation

## 🎯 Fixtures

Shared fixtures are defined in `conftest.py`:

### Data Fixtures
- `sample_verse_text` - Genesis 1:1 text
- `sample_tokens` - Token list for Genesis 1:1
- `sample_verse` - Complete Verse object with tokens
- `sample_verse_with_person` - Verse with person entity
- `sample_spans` - Sample labeled spans

### Configuration Fixtures
- `sample_label_config` - Minimal label rules config
- `sample_rules` - LabelRules instance
- `sample_label_config_with_phrases` - Config with phrases
- `sample_rules_with_phrases` - LabelRules with phrases

### Morphology Fixtures
- `sample_hebrew_morph` - Hebrew morphology code
- `sample_greek_morph` - Greek morphology code

### XML Fixtures
- `sample_step_xml` - STEP XML fragment

### File Fixtures
- `sample_gazetteer_file` - Temporary gazetteer file

## 🔧 Configuration

Test configuration is in `pytest.ini`:

```ini
[pytest]
testpaths = tests
addopts = -v --strict-markers --cov=code --cov-report=term-missing
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower)
    slow: Slow tests (>1 second)
    alignment: Alignment algorithm tests
    parsing: XML/morphology parsing tests
    labels: Label matching tests
```

## 📈 Coverage Targets

| Module | Current | Target |
|--------|---------|--------|
| `silver_alignment.py` | TBD | >95% |
| `silver_label_rules.py` | TBD | >90% |
| `silver_data_models.py` | TBD | >85% |
| `step_morph_parser.py` | TBD | >85% |
| `step_text_utils.py` | TBD | >80% |
| **Overall** | TBD | **>80%** |

Run `pytest --cov` to generate current coverage report.

## 🐛 Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'silver_data_models'`

**Solution**: Ensure you're running from project root or add code/ to PYTHONPATH:
```bash
set PYTHONPATH=%PYTHONPATH%;D:\Project_PP\projects\bible\code
pytest
```

### Missing Dependencies

**Problem**: `ModuleNotFoundError: No module named 'pytest'`

**Solution**: Install test dependencies:
```bash
pip install -r requirements-test.txt
```

### Test Failures

**Problem**: Tests fail with alignment errors

**Solution**: Check that the test fixtures match expected format:
```bash
pytest -v --tb=long tests/test_alignment.py
```

## 📚 Writing New Tests

### Template for New Tests

```python
import pytest
from silver_alignment import greedy_align_tokens_to_text

@pytest.mark.unit
@pytest.mark.alignment
def test_my_new_feature():
    """Test description."""
    # Arrange
    text = "In the beginning"
    tokens = ["In", "the", "beginning"]

    # Act
    spans, misses = greedy_align_tokens_to_text(text, tokens)

    # Assert
    assert misses == 0
    assert len(spans) == 3
```

### Best Practices

1. **Use descriptive test names**: `test_alignment_with_missing_token`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **One assertion focus per test**: Test one thing well
4. **Use fixtures**: Reuse common test data
5. **Add markers**: Categorize with @pytest.mark.*
6. **Document edge cases**: Explain tricky scenarios

## 🚀 CI/CD Integration

### GitHub Actions (Future)

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements-test.txt
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## 📞 Next Steps

1. Run all tests: `pytest`
2. Check coverage: `pytest --cov`
3. Fix any failures
4. Add more tests for uncovered code
5. Set up CI/CD pipeline

---

**Test Suite Created**: 2025-10-29 (Phase 3)
**Total Tests**: 39 tests
**Coverage Target**: >80%
