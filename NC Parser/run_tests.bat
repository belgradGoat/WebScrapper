@echo off
echo NC Parser - Quick Test
echo =====================

echo.
echo Testing basic functionality...
"%~dp0.venv\Scripts\python.exe" "%~dp0test_basic.py"

echo.
echo Running demo...
"%~dp0.venv\Scripts\python.exe" "%~dp0demo.py"

echo.
echo Tests completed!
pause
