@echo off
echo ======================================================================
echo BIBLE DATABASE ANALYTICS SUITE - Full Analysis
echo ======================================================================
echo.
echo Running all 7 analysis modules...
echo.

echo [1/7] Content Distribution Analysis...
python analyze_content.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Content analysis failed
    pause
    exit /b 1
)
echo.

echo [2/7] Theological Coverage Analysis...
python analyze_theology.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Theology analysis failed
    pause
    exit /b 1
)
echo.

echo [3/7] Cross-Reference Network Analysis...
python analyze_crossrefs.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Cross-reference analysis failed
    pause
    exit /b 1
)
echo.

echo [4/7] Difficulty Profile Analysis...
python analyze_difficulty.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Difficulty analysis failed
    pause
    exit /b 1
)
echo.

echo [5/7] Clue Quality Assessment...
python analyze_clues.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Clue analysis failed
    pause
    exit /b 1
)
echo.

echo [6/7] Completeness & Gap Analysis...
python analyze_completeness.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Completeness analysis failed
    pause
    exit /b 1
)
echo.

echo [7/7] Performance Benchmarks...
python analyze_performance.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Performance analysis failed
    pause
    exit /b 1
)
echo.

echo ======================================================================
echo All 7 analyses completed successfully!
echo ======================================================================
echo.

echo Generating Executive Report...
python generate_report.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Report generation failed
    pause
    exit /b 1
)
echo.

echo Exporting Dashboard Data...
python export_dashboard_data.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Dashboard export failed
    pause
    exit /b 1
)
echo.

echo ======================================================================
echo COMPLETE! All analyses and reports generated.
echo ======================================================================
echo.
echo Output location: ..\..\..\output\Analytics\
echo.
echo To view results:
echo 1. Open: ..\..\..\output\Analytics\bible_analytics_dashboard.html
echo 2. Review: ..\..\..\output\Analytics\executive_summary.json
echo.
pause
