@echo off
setlocal EnableDelayedExpansion
title Novel Agent - Installer
color 0B

cls
echo.
echo  ======================================================================
echo.
echo      NOVEL AGENT  -  AI POWERED WRITING ASSISTANT
echo.
echo               +------------------------+
echo               ^|   Installer v1.2.0     ^|
echo               +------------------------+
echo.
echo  ======================================================================
echo.

:: ============ Step 1: Check Python ============
echo  [1/5] Checking System Requirements...

python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo  [ERROR] Python is not installed or not in PATH.
    echo.
    echo  Please install Python 3.9 or higher from:
    echo  https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo        Found Python %PYTHON_VERSION% ... [OK]
echo.

:: ============ Step 2: Create Environment ============
echo  [2/5] Setting up Virtual Environment...

if not exist ".venv" (
    echo        Creating .venv directory...
    python -m venv .venv
    echo        Virtual environment created ... [OK]
) else (
    echo        Using existing .venv ... [OK]
)
echo.

:: ============ Step 3: Activate ============
echo  [3/5] Activating Environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    color 0C
    echo.
    echo  [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo        Environment activated ... [OK]
echo.

:: ============ Step 4: Upgrade Tools ============
echo  [4/5] Establishing Core Tools...
python -m pip install --upgrade pip -q
echo        Pip upgraded to latest version ... [OK]
echo.

:: ============ Step 5: Install Dependencies ============
echo  [5/5] Installing Libraries...
echo.
echo        Please wait, downloading packages (this may take a while)...
echo.

echo        [..        ] Google Generative AI SDK ...
pip install google-generativeai -q

echo        [....      ] ChromaDB Vector Database ...
pip install chromadb -q

echo        [......    ] Web Framework (Flask) ...
pip install flask flask-cors -q

echo        [........  ] Text Processing Tools ...
pip install jinja2 rich pyyaml python-dotenv -q

echo        [..........] Novel Agent Core ...
pip install -e . -q

if errorlevel 1 (
    color 0C
    echo.
    echo  [ERROR] Installation failed.
    echo.
    echo  Retrying in verbose mode to show errors:
    echo  ----------------------------------------
    pip install -e .
    pause
    exit /b 1
)
echo.
echo        All dependencies installed ... [OK]
echo.

:: ============ Config setup ============
if not exist ".env" (
    echo  [+] Configuration Setup
    echo      Creating default .env file...
    copy .env.example .env >nul 2>&1
    echo.
    echo      opening config file...
    start notepad .env
)

:: ============ Finish ============
color 0A
cls
echo.
echo  ======================================================================
echo.
echo      INSTALLATION SUCCESSFUL!
echo.
echo      What to do next:
echo      1. Ensure you added your API KEY in the opened .env file.
echo      2. Run 'start.bat' to launch the application.
echo.
echo  ======================================================================
echo.
pause
