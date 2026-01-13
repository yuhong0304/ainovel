@echo off
setlocal EnableDelayedExpansion
title Novel Agent - Launcher

cls
echo.
echo ================================================================
echo              Novel Agent - Launcher
echo              (Fanqie Novel AI Assistant)
echo ================================================================
echo.

:: Check venv
if not exist ".venv\Scripts\activate.bat" (
    echo [X] Virtual environment not found!
    echo     Please run install.bat first
    echo.
    pause
    exit /b 1
)

:: Check .env
if not exist ".env" (
    echo [X] .env config file not found!
    echo     Please copy .env.example to .env and add your API Key
    echo.
    pause
    exit /b 1
)

:: Activate venv
call .venv\Scripts\activate.bat

:menu
echo Select mode:
echo.
echo   [1] Web UI (recommended)
echo   [2] Command Line (CLI)
echo   [3] Development mode
echo   [0] Exit
echo.

set /p choice=Enter option (1/2/3/0): 

if "%choice%"=="1" goto web
if "%choice%"=="2" goto cli
if "%choice%"=="3" goto dev
if "%choice%"=="0" goto exit
goto invalid

:web
echo.
echo Starting Web UI...
echo   URL: http://localhost:5000
echo   Press Ctrl+C to stop
echo.
python -m novel_agent.web.app
goto end

:cli
echo.
echo Starting CLI mode...
echo.
python -m novel_agent.main
goto end

:dev
echo.
echo Starting development mode...
echo   URL: http://localhost:5000
echo.
set FLASK_DEBUG=1
python -m novel_agent.web.app
goto end

:invalid
echo [X] Invalid option
echo.
goto menu

:exit
echo Goodbye!
exit /b 0

:end
echo.
echo Program exited
pause
