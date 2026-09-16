@echo off
setlocal
cd /d "%~dp0"
if exist "ArrowGame.exe" (
    start "" "ArrowGame.exe"
    exit /b
)
if exist "dist\ArrowGame.exe" (
    start "" "dist\ArrowGame.exe"
    exit /b
)
if not exist ".venv\Scripts\python.exe" (
    py -3.13 -m venv .venv
    if errorlevel 1 (
        echo Python 3.13 is required for source mode. See README.md.
        pause
        exit /b 1
    )
)
".venv\Scripts\python.exe" -c "import pygame" >nul 2>nul
if errorlevel 1 (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        pause
        exit /b 1
    )
)
".venv\Scripts\python.exe" ArrowGame.py
if errorlevel 1 pause
