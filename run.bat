@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0" || exit /b 1

if not exist "venv\Scripts\python.exe" (
    echo Environnement virtuel introuvable.
    echo Executez d'abord setup.bat
    exit /b 1
)

call "venv\Scripts\activate.bat"
python app.py
