@echo off
title CHER-CDSS Platform Launcher - N-HYPPADEC
echo ======================================================================
echo   N-HYPPADEC CHER-CDSS DECISION-SUPPORT PLATFORM (v4.2)
echo   Starting Institutional Server...
echo ======================================================================

cd /d "%~dp0"

:: Check if virtual environment exists
if exist ".venv\Scripts\python.exe" (
    echo [OK] Virtual environment found.
    start "" http://127.0.0.1:8000/
    .venv\Scripts\python.exe run_dashboard.py
) else (
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe
    pause
)
