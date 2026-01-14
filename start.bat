@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: --- DEBUG START ---
echo Starting Novel Agent Launcher...
echo Current Directory: %CD%
:: -------------------

:: Check for .venv
if not exist ".venv\Scripts\python.exe" (
    color 0C
    echo [ERROR] Virtual Environment not found at .venv\Scripts\python.exe
    echo Please run 'install.bat' first.
    pause
    exit /b 1
)

:: Validate Python
".venv\Scripts\python.exe" --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Python executable in .venv is invalid or corrupt.
    pause
    exit /b 1
)

:: Set Paths
set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

:menu
cls
echo.
echo  ======================================================================
echo.
echo      NOVEL AGENT  -  AI POWERED WRITING ASSISTANT
echo.
echo               +------------------------+
echo               ^|    Launcher v1.2.1     ^|
echo               +------------------------+
echo.
echo  ======================================================================
echo.
echo  Debug: Python=%PYTHON_EXE%
echo.
echo      SELECT STARTUP MODE
echo      -------------------
echo.
echo    [1]  Web Interface (Recommended)
echo    [2]  Command Line Interface (CLI)
echo    [3]  Development Mode
echo    [0]  Exit
echo.

set /p choice=   Enter option (1/2/3/0): 

if "%choice%"=="1" goto web
if "%choice%"=="2" goto cli
if "%choice%"=="3" goto dev
if "%choice%"=="0" goto exit
goto invalid

:web
cls
echo ===================================================
echo   Starting Novel Agent (Web UI)...
echo ===================================================
echo.
echo   [1] Backend: Flask Server (Port 5000)
echo   [2] Frontend: Vite Dev Server (Port 5173)
echo.
echo   NOTE: Please ensure you have run 'npm run dev' in the frontend directory
echo         in a separate terminal window for the UI.
echo.

set FLASK_APP=src/novel_agent/web/app.py
set FLASK_ENV=development
"%PYTHON_EXE%" -m flask run --host=0.0.0.0 --port=5000
if errorlevel 1 pause
goto end

:cli
cls
echo Starting CLI Mode...
"%PYTHON_EXE%" -m novel_agent.main
if errorlevel 1 pause
goto end

:dev
cls
echo Starting Development Mode...
set FLASK_DEBUG=1
"%PYTHON_EXE%" -m novel_agent.web.app
if errorlevel 1 pause
goto end

:invalid
echo Invalid option.
pause
goto menu

:exit
echo Goodbye!
exit /b 0

:end
pause
