@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title Novel Agent - Installer & Updater
color 0B

cls
echo.
echo  ======================================================================
echo.
echo      NOVEL AGENT  -  AI POWERED WRITING ASSISTANT
echo.
echo               +------------------------+
echo               ^| Installer ^& Updater v1.2.1 ^|
echo               +------------------------+
echo.
echo  ======================================================================
echo.

:: ============ Step 0: Migration & Backup Checks ============
echo  [0/5] Checking for Existing Installation...

set "BACKUP_DIR=backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%"
set "BACKUP_DIR=%BACKUP_DIR: =0%"

if exist ".env" (
    echo.
    echo      [!] Detected existing configuration (.env)
    echo          Creating backup to .env.bak ...
    copy .env ".env.bak" >nul
    echo          Backup created.
)

if exist ".venv" (
    echo.
    echo      [!] Detected existing virtual environment (.venv)
    echo          It is recommended to UPDATE rather than reinstall.
    echo.
)

:: Clean old build artifacts to ensure clean migration
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "src\novel_agent.egg-info" rmdir /s /q "src\novel_agent.egg-info"
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

:: ============ Step 2: Create/Update Environment ============
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

:: ============ Step 3.5: Clean Corrupt Packages ============
echo  [3.5/5] Checking for Installation Residue...
if exist ".venv\Lib\site-packages" (
    pushd ".venv\Lib\site-packages"
    for /d %%i in (~*) do (
        echo        Cleaning up leftover: %%i
        rd /s /q "%%i" >nul 2>&1
    )
    popd
)
echo        Cleanup complete ... [OK]
echo.

:: ============ Step 4: Upgrade Tools ============
echo  [4/5] Establishing Core Tools...
python -m pip install --upgrade pip -q
echo        Pip upgraded to latest version ... [OK]
echo.

:: ============ Step 5: Install/Migrate Dependencies ============
echo  [5/5] Installing/Updating Libraries...
echo.
echo        Please wait, downloading packages (this may take a while)...
echo.

echo        [..        ] Google Generative AI SDK ...
pip install google-generativeai --upgrade -q

echo        [....      ] ChromaDB Vector Database ...
pip install chromadb --upgrade -q

echo        [......    ] Web Framework (Flask) ...
pip install flask flask-cors --upgrade -q

echo        [........  ] Text Processing Tools ...
pip install jinja2 rich pyyaml python-dotenv --upgrade -q

echo        [..........] Novel Agent Core (Force Reinstall + All Features) ...
:: Use --force-reinstall and [full] to ensure all dependencies (Export, OpenAI, Claude) are installed
pip install -e .[full] --force-reinstall -q

if errorlevel 1 (
    color 0C
    echo.
    echo  [ERROR] Installation failed.
    echo.
    echo  Retrying in verbose mode to show errors:
    echo  ----------------------------------------
    pip install -e .[full] --force-reinstall
    pause
    exit /b 1
)
echo.
echo        All dependencies installed ... [OK]
echo.

:: ============ Config setup ============
if not exist ".env" (
    if exist ".env.bak" (
        echo  [+] Restoring Configuration
        echo      Restoring .env from backup...
        copy ".env.bak" .env >nul
    ) else (
        echo  [+] Configuration Setup
        echo      Creating default .env file...
        copy .env.example .env >nul 2>&1
        echo.
        echo      opening config file...
        start notepad .env
    )
)

:: ============ Finish ============
color 0A
cls
echo.
echo  ======================================================================
echo.
echo      INSTALLATION / MIGRATION SUCCESSFUL!
echo.
echo      Migration Notes:
echo      - Your previous configuration was backed up to .env.bak
echo      - Your projects data in 'projects/' directory is safe.
echo      - Old build artifacts were cleaned up.
echo.
echo      [中文提示]
echo      安装/更新已完成！
echo      - 配置文件已备份 (.env.bak)
echo      - 项目数据已保留
echo      请运行 'start.bat' 启动程序。
echo.
echo      What to do next:
echo      1. Run 'start.bat' to launch the application.
echo.
echo  ======================================================================
echo.
pause
