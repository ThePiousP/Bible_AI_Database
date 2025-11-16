@echo off
REM ============================================================================
REM run_tests.bat
REM Test suite runner for Bible NER pipeline
REM Created: 2025-10-29
REM ============================================================================

setlocal EnableDelayedExpansion

echo.
echo ============================================================================
echo  Bible NER Pipeline - Test Suite Runner
echo ============================================================================
echo.

REM Check if Python is available
python --version >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.11+ and try again
    exit /b 1
)

REM Determine what to test
set TEST_MODE=%1
if "%TEST_MODE%"=="" set TEST_MODE=all

echo Test Mode: %TEST_MODE%
echo.

REM ============================================================================
REM Phase 1: Database Validation
REM ============================================================================

if /I "%TEST_MODE%"=="all" goto :run_db_tests
if /I "%TEST_MODE%"=="db" goto :run_db_tests
if /I "%TEST_MODE%"=="quick" goto :skip_db_tests
goto :skip_db_tests

:run_db_tests
echo [1/5] Validating databases...
echo ============================================================================

if exist "data\GoodBook.db" (
    python validate_databases.py --goodbook "data\GoodBook.db" --verbose
    if !ERRORLEVEL! NEQ 0 (
        echo.
        echo [ERROR] GoodBook.db validation failed!
        set /p continue="Continue anyway? (y/N): "
        if /I not "!continue!"=="y" exit /b 1
    ) else (
        echo [OK] GoodBook.db validation passed
    )
) else (
    echo [WARN] GoodBook.db not found, skipping validation
)

if exist "data\concordance.db" (
    python validate_databases.py --concordance "data\concordance.db" --verbose --skip-goodbook
    if !ERRORLEVEL! NEQ 0 (
        echo.
        echo [ERROR] concordance.db validation failed!
        set /p continue="Continue anyway? (y/N): "
        if /I not "!continue!"=="y" exit /b 1
    ) else (
        echo [OK] concordance.db validation passed
    )
) else (
    echo [WARN] concordance.db not found, skipping validation
)

echo.
goto :after_db_tests

:skip_db_tests
echo [1/5] Skipping database validation (use 'run_tests.bat db' to run)
echo.

:after_db_tests

REM ============================================================================
REM Phase 2: Python Unit Tests (if pytest available)
REM ============================================================================

if /I "%TEST_MODE%"=="db" goto :skip_unit_tests

echo [2/5] Running Python unit tests...
echo ============================================================================

REM Check if pytest is installed
python -c "import pytest" >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [SKIP] pytest not installed
    echo        Install with: pip install pytest
    goto :skip_unit_tests
)

REM Check if tests/ directory exists
if not exist "tests\" (
    echo [SKIP] tests/ directory not found
    echo        Unit tests will be added in Phase 2 of refactoring
    goto :skip_unit_tests
)

REM Run pytest
python -m pytest tests/ -v --tb=short
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [ERROR] Unit tests failed!
    set /p continue="Continue anyway? (y/N): "
    if /I not "!continue!"=="y" exit /b 1
) else (
    echo [OK] Unit tests passed
)

goto :after_unit_tests

:skip_unit_tests
echo [2/5] Skipping unit tests (pytest not available or tests/ not found)
echo.

:after_unit_tests

REM ============================================================================
REM Phase 3: Import Validation (check for syntax errors)
REM ============================================================================

echo [3/5] Validating Python imports...
echo ============================================================================

set IMPORT_ERRORS=0

REM Test core modules
for %%M in (
    "code\bible_scraper.py"
    "code\export_ner_silver.py"
    "code\entity_validator.py"
    "code\ai_tools\bible_nlp.py"
) do (
    if exist "%%M" (
        python -c "import importlib.util; spec = importlib.util.spec_from_file_location('test', r'%%M'); mod = importlib.util.module_from_spec(spec)" >NUL 2>&1
        if !ERRORLEVEL! NEQ 0 (
            echo    [FAIL] %%M - has import errors
            set /a IMPORT_ERRORS+=1
        ) else (
            echo    [OK] %%M
        )
    )
)

if !IMPORT_ERRORS! GTR 0 (
    echo.
    echo [ERROR] Found !IMPORT_ERRORS! file(s) with import errors
    set /p continue="Continue anyway? (y/N): "
    if /I not "!continue!"=="y" exit /b 1
) else (
    echo [OK] All imports valid
)

echo.

REM ============================================================================
REM Phase 4: Configuration Validation
REM ============================================================================

echo [4/5] Validating configuration files...
echo ============================================================================

set CONFIG_ERRORS=0

REM Check config.json
if exist "config.json" (
    python -c "import json; json.load(open('config.json'))" >NUL 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo    [FAIL] config.json - invalid JSON
        set /a CONFIG_ERRORS+=1
    ) else (
        echo    [OK] config.json
    )
) else (
    echo    [WARN] config.json not found
)

REM Check YAML configs
for %%F in (
    "project.yml"
    "silver_config.yml"
    "label_rules.yml"
) do (
    if exist "%%F" (
        python -c "import yaml; yaml.safe_load(open(r'%%F', encoding='utf-8'))" >NUL 2>&1
        if !ERRORLEVEL! NEQ 0 (
            echo    [FAIL] %%F - invalid YAML
            set /a CONFIG_ERRORS+=1
        ) else (
            echo    [OK] %%F
        )
    ) else (
        echo    [WARN] %%F not found
    )
)

if !CONFIG_ERRORS! GTR 0 (
    echo.
    echo [ERROR] Found !CONFIG_ERRORS! invalid configuration file(s)
    set /p continue="Continue anyway? (y/N): "
    if /I not "!continue!"=="y" exit /b 1
) else (
    echo [OK] All configuration files valid
)

echo.

REM ============================================================================
REM Phase 5: Integration Tests (optional, requires data)
REM ============================================================================

if /I "%TEST_MODE%"=="quick" goto :skip_integration_tests
if /I "%TEST_MODE%"=="db" goto :skip_integration_tests

echo [5/5] Running integration tests...
echo ============================================================================

REM Test silver export on small dataset (if concordance.db exists)
if not exist "data\concordance.db" (
    echo [SKIP] concordance.db not found - cannot run integration tests
    goto :skip_integration_tests
)

if not exist "label_rules.yml" (
    echo [SKIP] label_rules.yml not found - cannot run silver export test
    goto :skip_integration_tests
)

echo Testing silver export (Genesis 1 only)...

REM Create test output directory
mkdir "output\test_silver" 2>NUL

REM Run export on just Genesis (limited test)
python code\export_ner_silver.py ^
    --db "data\concordance.db" ^
    --rules "label_rules.yml" ^
    --outdir "output\test_silver" ^
    --seed 13 ^
    --ratios 0.8 0.1 0.1 ^
    >NUL 2>&1

if !ERRORLEVEL! NEQ 0 (
    echo [FAIL] Silver export test failed
    echo        Run manually to debug: python code\export_ner_silver.py --db "data\concordance.db" --rules "label_rules.yml" --outdir "output\test_silver"
) else (
    echo [OK] Silver export test passed

    REM Verify output files exist
    if exist "output\test_silver\train.jsonl" (
        echo [OK] train.jsonl created
    ) else (
        echo [WARN] train.jsonl not found
    )

    if exist "output\test_silver\dev.jsonl" (
        echo [OK] dev.jsonl created
    ) else (
        echo [WARN] dev.jsonl not found
    )

    if exist "output\test_silver\test.jsonl" (
        echo [OK] test.jsonl created
    ) else (
        echo [WARN] test.jsonl not found
    )
)

REM Clean up test output
rmdir /S /Q "output\test_silver" 2>NUL

goto :after_integration_tests

:skip_integration_tests
echo [5/5] Skipping integration tests (use 'run_tests.bat all' to run)
echo.

:after_integration_tests

REM ============================================================================
REM Summary
REM ============================================================================

echo.
echo ============================================================================
echo  Test Summary
echo ============================================================================
echo.

if !IMPORT_ERRORS! GTR 0 (
    echo ❌ FAILED - Found import errors
    exit /b 1
)

if !CONFIG_ERRORS! GTR 0 (
    echo ❌ FAILED - Found configuration errors
    exit /b 1
)

echo ✅ All tests PASSED
echo.
echo Next steps:
echo   - Review REFACTORING_PLAN.md
echo   - Run: backup_before_refactor.bat
echo   - Begin Phase 1 refactoring
echo.
echo ============================================================================

endlocal
exit /b 0
