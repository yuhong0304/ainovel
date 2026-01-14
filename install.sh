#!/bin/bash
# 番茄小说Agent - 一键安装脚本 (Linux/Mac)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

clear
echo ""
echo -e "${CYAN}======================================================================${NC}"
echo ""
echo -e "${CYAN}      NOVEL AGENT  -  AI POWERED WRITING ASSISTANT${NC}"
echo ""
echo -e "${CYAN}               +------------------------+${NC}"
echo -e "${CYAN}               | Installer v1.2.1     |${NC}"
echo -e "${CYAN}               +------------------------+${NC}"
echo ""
echo -e "${CYAN}======================================================================${NC}"
echo ""

# Check Python
echo -e "${BLUE}[1/5] Checking System Requirements...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed.${NC}"
    echo "Please install Python 3.9+ and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "      Found Python $PYTHON_VERSION ... ${GREEN}[OK]${NC}"
echo ""

# Create venv
echo -e "${BLUE}[2/5] Setting up Virtual Environment...${NC}"
if [ ! -d ".venv" ]; then
    echo "      Creating .venv directory..."
    python3 -m venv .venv
    echo -e "      Virtual environment created ... ${GREEN}[OK]${NC}"
else
    echo -e "      Using existing .venv ... ${GREEN}[OK]${NC}"
fi
echo ""

# Activate venv
echo -e "${BLUE}[3/5] Activating Environment...${NC}"
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to activate virtual environment.${NC}"
    exit 1
fi
echo -e "      Environment activated ... ${GREEN}[OK]${NC}"
echo ""

# Upgrade pip
echo -e "${BLUE}[4/5] Establishing Core Tools...${NC}"
pip install --upgrade pip -q
echo -e "      Pip upgraded to latest version ... ${GREEN}[OK]${NC}"
echo ""

# Install dependencies (Migrate logic)
echo -e "${BLUE}[5/5] Installing/Updating Libraries...${NC}"
echo ""
echo "      Please wait, downloading packages..."
echo ""

echo -e "      [..        ] Google Generative AI SDK"
pip install google-generativeai --upgrade -q

echo -e "      [....      ] ChromaDB Vector Database"
pip install chromadb --upgrade -q

echo -e "      [......    ] Web Framework (Flask)"
pip install flask flask-cors --upgrade -q

echo -e "      [........  ] Text Processing Tools"
pip install jinja2 rich pyyaml python-dotenv --upgrade -q

echo -e "      [..........] Novel Agent Core (Full Features)"
# Install with [full] to support Export, OpenAI, etc.
pip install -e .[full] --upgrade -q

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[ERROR] Installation failed.${NC}"
    echo "Retrying in verbose mode to show errors:"
    pip install -e .[full]
    exit 1
fi

echo ""
echo -e "      All dependencies installed ... ${GREEN}[OK]${NC}"
echo ""

# Check .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[+] Configuration Setup${NC}"
    echo "    Creating default .env file..."
    cp .env.example .env
    echo -e "    ${GREEN}[OK] .env file created${NC}"
    echo ""
    echo "    Run the following command to edit configuration:"
    echo -e "    ${YELLOW}nano .env${NC}"
fi

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${GREEN}      INSTALLATION SUCCESSFUL!${NC}"
echo ""
echo "      What to do next:"
echo "      1. Ensure you added your API KEY in the .env file"
echo "      2. Run './start.sh' to launch the application"
echo ""
echo -e "${GREEN}======================================================================${NC}"
echo ""
