@echo off
setlocal EnableDelayedExpansion
title Novel Agent - Installer

cls
echo.
echo ================================================================
echo          Novel Agent - One-Click Installer v1.1
echo          (Fanqie Novel AI Assistant)
echo ================================================================
echo.

:: ============ Step 1: Check Python ============
echo ----------------------------------------------------------------
echo  [1/5] Checking Python...
echo ----------------------------------------------------------------

python --version >nul 2>&1
if errorlevel 1 (
    echo    [X] Python not found! Please install Python 3.9+
    echo        Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo    [OK] Python %PYTHON_VERSION%

:: ============ Step 2: Create venv ============
echo.
echo ----------------------------------------------------------------
echo  [2/5] Creating virtual environment...
echo ----------------------------------------------------------------

if not exist ".venv" (
    echo    [...] Creating venv...
    python -m venv .venv
    echo    [OK] Virtual environment created
) else (
    echo    [OK] Virtual environment exists
)

:: ============ Step 3: Activate venv ============
echo.
echo ----------------------------------------------------------------
echo  [3/5] Activating virtual environment...
echo ----------------------------------------------------------------
call .venv\Scripts\activate.bat
echo    [OK] Activated

:: ============ Step 4: Upgrade pip ============
echo.
echo ----------------------------------------------------------------
echo  [4/5] Upgrading pip...
echo ----------------------------------------------------------------
echo    [...] Upgrading...
python -m pip install --upgrade pip -q
echo    [OK] pip is up to date

:: ============ Step 5: Install dependencies ============
echo.
echo ----------------------------------------------------------------
echo  [5/5] Installing dependencies...
echo ----------------------------------------------------------------
echo.
echo    This may take a few minutes...
echo.
echo    [##--------] 10%% - google-generativeai
pip install google-generativeai -q
echo    [####------] 20%% - chromadb
pip install chromadb -q
echo    [#####-----] 30%% - flask
pip install flask flask-cors -q
echo    [######----] 40%% - jinja2
pip install jinja2 -q
echo    [#######---] 50%% - rich
pip install rich -q
echo    [########--] 60%% - pyyaml
pip install pyyaml python-dotenv -q
echo    [#########-] 70%% - installing project
pip install -e . -q
if errorlevel 1 (
    echo.
    echo    [X] Installation failed! Showing details...
    echo.
    pip install -e .
    pause
    exit /b 1
)
echo    [##########] 100%% - Done!
echo.
echo    [OK] All dependencies installed

:: ============ Complete ============
echo.
echo ================================================================
echo                    Installation Complete!
echo ================================================================
echo.
echo  Next steps:
echo    1. Edit .env file and add your GEMINI_API_KEY
echo    2. Double-click start.bat to run
echo.
echo  Get API Key at:
echo    https://aistudio.google.com/app/apikey
echo.
echo ================================================================
echo.

:: Create .env if needed
if not exist ".env" (
    echo [!] Creating .env config file...
    copy .env.example .env >nul 2>&1
    echo [OK] .env file created
    echo.
    echo Press any key to open .env for editing...
    pause >nul
    notepad .env
) else (
    echo [OK] .env config file exists
)

echo.
echo Now you can double-click start.bat to run!
echo.
pause
