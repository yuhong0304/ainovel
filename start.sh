#!/bin/bash
# 番茄小说Agent - 启动脚本 (Linux/Mac)

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              📚 番茄小说Agent - 启动器                       ║"
echo "║              Novel Agent - Launcher                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检查虚拟环境
if [ ! -f ".venv/bin/activate" ]; then
    echo "❌ 未检测到虚拟环境！请先运行 ./install.sh 进行安装"
    exit 1
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "❌ 未检测到 .env 配置文件！"
    echo "   请复制 .env.example 为 .env 并填入你的 API Key"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

echo "请选择启动模式:"
echo ""
echo "  [1] 🌐 Web 界面模式 (推荐)"
echo "  [2] 💻 命令行模式 (CLI)"
echo "  [3] 🔧 开发模式 (热重载)"
echo "  [0] 退出"
echo ""

read -p "请输入选项 (1/2/3/0): " choice

case $choice in
    1)
        echo ""
        echo "🚀 启动 Web 界面..."
        echo "   访问地址: http://localhost:5000"
        echo "   按 Ctrl+C 停止服务"
        echo ""
        novel-web
        ;;
    2)
        echo ""
        echo "🚀 启动命令行模式..."
        echo ""
        novel-agent
        ;;
    3)
        echo ""
        echo "🚀 启动开发模式 (热重载)..."
        echo "   访问地址: http://localhost:5000"
        echo ""
        python -m novel_agent.web.app
        ;;
    0)
        echo "再见! 👋"
        exit 0
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
