@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0" || exit /b 1

echo MCP Assistant Local - Setup Windows
echo ====================================

where python >nul 2>nul
if errorlevel 1 (
    echo Python n'est pas installe ou n'est pas dans le PATH.
    exit /b 1
)

for /f "delims=" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo !PYTHON_VERSION! trouve

if not exist "venv\Scripts\python.exe" (
    echo Creation de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 (
        echo Echec de creation du venv.
        exit /b 1
    )
)

echo Installation des dependances...
"venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo Echec de la mise a jour de pip.
    exit /b 1
)

"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Echec de l'installation des dependances.
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" >nul
        echo Fichier .env cree depuis .env.example.
    ) else (
        echo Fichier .env introuvable et .env.example absent.
    )
) else (
    echo Fichier .env trouve.
)

echo.
echo Setup termine.
echo Pour demarrer: run.bat
