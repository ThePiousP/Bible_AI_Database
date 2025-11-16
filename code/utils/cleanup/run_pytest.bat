@echo off
REM ============================================================================
REM run_pytest.bat
REM pytest test runner for Bible NER Pipeline (Phase 3)
REM Usage:
REM   run_pytest.bat          - Run all tests
REM   run_pytest.bat quick    - Run only unit tests
REM   run_pytest.bat coverage - Run with coverage report
REM   run_pytest.bat alignment - Run only alignment tests
REM   run_pytest.bat labels    - Run only label rules tests
REM   run_pytest.bat parsing   - Run only parsing tests
REM ============================================================================

setlocal EnableDelayedExpansion

echo.
echo ============================================================================
echo Bible NER Pipeline - pytest Test Suite
echo ============================================================================
echo.

REM Check if Python is available
python --version >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.11+ and try again
    exit /b 1
)

REM Check if pytest is installed
python -c "import pytest" >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] pytest not installed
    echo.
    echo Install with: pip install -r requirements-test.txt
    echo.
    pause
    exit /b 1
)

REM Check if tests/ directory exists
if not exist "tests\" (
    echo [ERROR] tests/ directory not found
    echo.
    pause
    exit /b 1
)

REM Parse command line argument
set MODE=%1

if "%MODE%"=="" set MODE=all
if "%MODE%"=="quick" goto QUICK
if "%MODE%"=="slow" goto SLOW
if "%MODE%"=="coverage" goto COVERAGE
if "%MODE%"=="cov" goto COVERAGE
if "%MODE%"=="alignment" goto ALIGNMENT
if "%MODE%"=="labels" goto LABELS
if "%MODE%"=="parsing" goto PARSING
if "%MODE%"=="all" goto ALL
if "%MODE%"=="verbose" goto VERBOSE
if "%MODE%"=="-v" goto VERBOSE
if "%MODE%"=="parallel" goto PARALLEL

echo Unknown mode: %MODE%
echo.
echo Valid modes:
echo   all        - Run all tests
echo   quick      - Run only unit tests (fast)
echo   slow       - Run all tests including slow ones
echo   coverage   - Run with coverage report
echo   alignment  - Run only alignment tests
echo   labels     - Run only label rules tests
echo   parsing    - Run only parsing tests
echo   verbose    - Run with verbose output
echo   parallel   - Run tests in parallel (faster)
echo.
pause
exit /b 1

:QUICK
echo Running quick tests (unit tests only)...
echo.
pytest -v -m "unit" tests/
goto END

:SLOW
echo Running all tests (including slow tests)...
echo.
pytest -v tests/
goto END

:COVERAGE
echo Running tests with coverage report...
echo.
pytest -v --cov=code --cov-report=term-missing --cov-report=html tests/
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================================
    echo Coverage report generated!
    echo ============================================================================
    echo.
    echo Open htmlcov/index.html in your browser to view the detailed report.
    echo.
    echo Quick stats:
    python -m coverage report --skip-covered
)
goto END

:ALIGNMENT
echo Running alignment tests only...
echo.
pytest -v -m "alignment" tests/test_alignment.py
goto END

:LABELS
echo Running label rules tests only...
echo.
pytest -v -m "labels" tests/test_label_rules.py
goto END

:PARSING
echo Running parsing tests only...
echo.
pytest -v -m "parsing" tests/test_step_parser.py
goto END

:VERBOSE
echo Running all tests with verbose output...
echo.
pytest -vv -ra tests/
goto END

:PARALLEL
echo Running tests in parallel...
echo.
REM Check if pytest-xdist is installed
python -c "import xdist" >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] pytest-xdist not installed - running tests sequentially
    echo        Install with: pip install pytest-xdist
    echo.
    pytest -v tests/
) else (
    pytest -v -n auto tests/
)
goto END

:ALL
echo Running all tests...
echo.
pytest -v tests/
goto END

:END
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================================
    echo ✅ All tests PASSED
    echo ============================================================================
) else (
    echo.
    echo ============================================================================
    echo ❌ Some tests FAILED
    echo ============================================================================
    echo.
    echo Run with verbose mode to see details: run_pytest.bat verbose
)

echo.
endlocal
exit /b %ERRORLEVEL%
