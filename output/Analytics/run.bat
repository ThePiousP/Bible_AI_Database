@echo off
echo ======================================================================
echo Starting Local Web Server for Bible Analytics Dashboard
echo ======================================================================
echo.
echo The dashboard will be available at:
echo http://localhost:8002/bible_analytics_dashboard.html
echo.
echo Press Ctrl+C to stop the server when done.
echo ======================================================================
echo.

REM Start Python HTTP server on port 8002
python -m http.server 8002

pause
