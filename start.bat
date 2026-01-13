@echo off
chcp 65001 >nul
title 番茄小说Agent - 启动器

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              📚 番茄小说Agent - 启动器                       ║
echo ║              Novel Agent - Launcher                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ 未检测到虚拟环境！请先运行 install.bat 进行安装
    echo.
    pause
    exit /b 1
)

:: 检查 .env 文件
if not exist ".env" (
    echo ❌ 未检测到 .env 配置文件！
    echo    请复制 .env.example 为 .env 并填入你的 API Key
    echo.
    pause
    exit /b 1
)

:: 激活虚拟环境
call .venv\Scripts\activate.bat

:menu
echo 请选择启动模式:
echo.
echo   [1] 🌐 Web 界面模式 (推荐)
echo   [2] 💻 命令行模式 (CLI)
echo   [3] 🔧 开发模式 (热重载)
echo   [0] 退出
echo.

set /p choice=请输入选项 (1/2/3/0): 

if "%choice%"=="1" goto web
if "%choice%"=="2" goto cli
if "%choice%"=="3" goto dev
if "%choice%"=="0" goto exit
goto invalid

:web
echo.
echo 🚀 启动 Web 界面...
echo    访问地址: http://localhost:5000
echo    按 Ctrl+C 停止服务
echo.
python -m novel_agent.web.app
goto end

:cli
echo.
echo 🚀 启动命令行模式...
echo.
python -m novel_agent.main
goto end

:dev
echo.
echo 🚀 启动开发模式 (热重载)...
echo    访问地址: http://localhost:5000
echo.
set FLASK_DEBUG=1
python -m novel_agent.web.app
goto end

:invalid
echo ❌ 无效选项，请重新选择
echo.
goto menu

:exit
echo 再见! 👋
exit /b 0

:end
echo.
echo 程序已退出
pause
