#!/bin/bash
cd "$(dirname "$0")"
# 番茄小说Agent - 启动脚本 (Linux/Mac)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check venv
if [ ! -f ".venv/bin/activate" ]; then
    echo -e "${RED}[ERROR] Virtual environment not found.${NC}"
    echo "Please run ./install.sh first to set up the environment."
    exit 1
fi

# Check .env
if [ ! -f ".env" ]; then
    echo -e "${RED}[ERROR] Configuration file (.env) missing.${NC}"
    echo "Please copy '.env.example' to '.env' and add your API keys."
    exit 1
fi

# Activate venv
source .venv/bin/activate
PYTHON_EXE="$(pwd)/.venv/bin/python3"
export PYTHONPATH=src:$PYTHONPATH

while true; do
    clear
    echo ""
    echo -e "${CYAN}======================================================================${NC}"
    echo ""
    echo -e "${CYAN}      NOVEL AGENT  -  AI POWERED WRITING ASSISTANT${NC}"
    echo ""
    echo -e "${CYAN}               +------------------------+${NC}"
    echo -e "${CYAN}               |    Launcher v1.2.0     |${NC}"
    echo -e "${CYAN}               +------------------------+${NC}"
    echo ""
    echo -e "${CYAN}======================================================================${NC}"
    echo ""
    echo "    Select Startup Mode:"
    echo "    -------------------"
    echo ""
    echo -e "    ${GREEN}[1] Web Interface (Recommended)${NC}"
    echo "        - Starts the local web server at http://localhost:5000"
    echo "        - Best for most users."
    echo ""
    echo -e "    ${YELLOW}[2] Command Line Interface (CLI)${NC}"
    echo "        - Text-based interactive mode."
    echo ""
    echo -e "    ${BLUE}[3] Development Mode${NC}"
    echo "        - Starts with debug features and hot-reloading."
    echo ""
    echo "    [0] Exit"
    echo ""
    echo -e "${CYAN}======================================================================${NC}"
    echo ""
    
    read -p "    Enter option (1/2/3/0): " choice

    case $choice in
        1)
            clear
            echo ""
            echo -e "${GREEN}======================================================================${NC}"
            echo -e "${GREEN}  Starting Web Interface...${NC}"
            echo -e "${GREEN}======================================================================${NC}"
            echo ""
            echo "  URL: http://localhost:5000"
            echo ""
            echo "  (Press Ctrl+C to stop the server)"
            echo ""
            "$PYTHON_EXE" -m novel_agent.web.app
            read -p "Press Enter to return to menu..."
            ;;
        2)
            clear
            echo ""
            echo -e "${YELLOW}======================================================================${NC}"
            echo -e "${YELLOW}  Starting CLI Mode...${NC}"
            echo -e "${YELLOW}======================================================================${NC}"
            echo ""
            "$PYTHON_EXE" -m novel_agent.main
            read -p "Press Enter to return to menu..."
            ;;
        3)
            clear
            echo ""
            echo -e "${BLUE}======================================================================${NC}"
            echo -e "${BLUE}  Starting Development Mode (Debug ON)...${NC}"
            echo -e "${BLUE}======================================================================${NC}"
            echo ""
            echo "  URL: http://localhost:5000"
            echo ""
            # Set FLASK_DEBUG for the session
            export FLASK_DEBUG=1
            "$PYTHON_EXE" -m novel_agent.web.app
            read -p "Press Enter to return to menu..."
            ;;
        0)
            echo ""
            echo "Goodbye! 👋"
            exit 0
            ;;
        *)
            echo ""
            echo -e "${RED}[!] Invalid option selected. Please try again.${NC}"
            sleep 1
            ;;
    esac
done
