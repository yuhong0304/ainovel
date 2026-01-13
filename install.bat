@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title 番茄小说Agent - 一键安装

:: 颜色设置
color 0F

cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║         📚 番茄小说Agent - 一键安装程序 v1.1                 ║
echo ║         Novel Agent - One-Click Installer                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: ============ 步骤 1: 检查 Python ============
call :step "检查 Python 环境" 1 5

python --version >nul 2>&1
if errorlevel 1 (
    call :error "未检测到 Python！请先安装 Python 3.9+"
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
call :success "Python %PYTHON_VERSION%"

:: ============ 步骤 2: 创建虚拟环境 ============
call :step "创建虚拟环境" 2 5

if not exist ".venv" (
    call :progress_start "创建中"
    python -m venv .venv 2>nul
    call :progress_end
    call :success "虚拟环境创建完成"
) else (
    call :success "虚拟环境已存在"
)

:: ============ 步骤 3: 激活虚拟环境 ============
call :step "激活虚拟环境" 3 5
call .venv\Scripts\activate.bat
call :success "已激活"

:: ============ 步骤 4: 升级 pip ============
call :step "升级 pip" 4 5
call :progress_start "升级中"
python -m pip install --upgrade pip -q 2>nul
call :progress_end
call :success "pip 已是最新"

:: ============ 步骤 5: 安装依赖 ============
call :step "安装项目依赖" 5 5
echo.
echo    正在安装依赖包，请稍候...
echo.

:: 显示安装进度
call :install_with_progress

if errorlevel 1 (
    call :error "安装依赖失败！"
    pause
    exit /b 1
)

call :success "所有依赖安装完成"

:: ============ 完成 ============
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                     ✅ 安装完成!                             ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║                                                              ║
echo ║  📋 下一步:                                                  ║
echo ║     1. 编辑 .env 文件，填入你的 GEMINI_API_KEY               ║
echo ║     2. 双击 start.bat 启动程序                               ║
echo ║                                                              ║
echo ║  🌐 获取 API Key:                                            ║
echo ║     https://aistudio.google.com/app/apikey                   ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: 检查并创建 .env 文件
if not exist ".env" (
    echo ⚠️  正在创建 .env 配置文件...
    copy .env.example .env >nul 2>&1
    echo ✅ 已创建 .env 文件
    echo.
    echo    按任意键打开配置文件进行编辑...
    pause >nul
    notepad .env
) else (
    echo ✅ .env 配置文件已存在
)

echo.
echo 🎉 现在可以双击 start.bat 启动程序了！
echo.
pause
exit /b 0

:: ============ 函数定义 ============

:step
echo.
echo ────────────────────────────────────────────────────────────────
echo  [%~2/%~3] %~1
echo ────────────────────────────────────────────────────────────────
goto :eof

:success
echo    ✅ %~1
goto :eof

:error
echo    ❌ %~1
goto :eof

:progress_start
set "progress_msg=%~1"
<nul set /p "=   ⏳ %progress_msg% "
goto :eof

:progress_end
echo ✓
goto :eof

:install_with_progress
:: 第一阶段：安装基础依赖
<nul set /p "=   [░░░░░░░░░░░░░░░░░░░░] 0%% - 准备中..."
timeout /t 1 >nul
<nul set /p "="

:: 安装主包
pip install -e . -q 2>nul
if errorlevel 1 exit /b 1

<nul set /p "=   [████████████████████] 100%% - 完成!   "
echo.
goto :eof
