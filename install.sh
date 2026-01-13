#!/bin/bash
# 番茄小说Agent - 一键安装脚本 (Linux/Mac)

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         📚 番茄小说Agent - 一键安装程序                      ║"
echo "║         Novel Agent - One-Click Installer                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检查 Python
echo "[1/5] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未检测到 Python3！请先安装 Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✅ 检测到 Python $PYTHON_VERSION"

# 创建虚拟环境
echo ""
echo "[2/5] 创建虚拟环境..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "[3/5] 激活虚拟环境..."
source .venv/bin/activate

# 升级 pip
echo ""
echo "[4/5] 升级 pip..."
pip install --upgrade pip -q

# 安装依赖
echo ""
echo "[5/5] 安装项目依赖..."
pip install -e . -q

if [ $? -ne 0 ]; then
    echo "❌ 安装依赖失败！"
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     ✅ 安装完成!                             ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  下一步:                                                     ║"
echo "║  1. 复制 .env.example 为 .env                                ║"
echo "║  2. 在 .env 中填入你的 GEMINI_API_KEY                        ║"
echo "║  3. 运行 ./start.sh 启动程序                                 ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  检测到 .env 文件不存在，正在从模板创建..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请编辑填入你的 API Key"
    echo ""
    echo "运行以下命令编辑配置文件:"
    echo "  nano .env"
fi

echo ""
echo "安装完成! 运行 './start.sh' 启动程序"
