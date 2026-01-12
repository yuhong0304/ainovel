# 📚 Novel Agent (番茄小说/网文 AI 助手)

> 一个基于 Gemini API 和 ChromaDB 的半自动化网文创作系统。
> 从灵感到大纲，从大纲到正文，全程 RAG (检索增强生成) 辅助，让 AI 真正读懂你的设定。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![Gemini](https://img.shields.io/badge/LLM-Gemini%203.0%20Pro-orange.svg)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)

## ✨ 核心特性

**🚀 完整流水线**: 灵感 -> 总纲 -> 卷纲 -> 章纲 -> 正文 -> 润色，全流程覆盖。
**🧠 真实记忆 (RAG)**: 使用 `ChromaDB` 向量数据库，自动索引人物小传、世界观设定和通过文，AI 写第100章时依然记得第1章的伏笔。
**💻 Web UI**: 全功能 Web 界面，支持分屏写作、状态监控、一键生成。

## 🛠️ 安装指南

### 1. 环境要求
- Windows (推荐), Linux, macOS
- Python 3.9+
- [Google Gemini API Key](https://aistudio.google.com/)

### 2. 克隆与安装

```bash
# 1. 克隆项目 (或下载源码)
git clone https://github.com/yuhong0304/ainovel.git
cd ainovel

# 2. 创建并激活虚拟环境 (推荐)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -e .
```

### 3. 配置
在项目根目录创建 `.env` 文件：

```ini
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-pro  # 支持 gemini-3.0-pro (experimental)
```

## 🚀 快速开始

### 1. 启动 Web 界面 (推荐)
安装完成后，直接运行：
```bash
novel-web
```
浏览器自动访问 `http://localhost:5000`。
Web 界面提供完整的创作流管理、分屏编辑和实时预览功能。

### 2. 命令行模式 (CLI)
如果你更习惯命令行交互：
```bash
novel-agent
```
按提示输入指令即可进行创作。

### 3. 本地开发
如果你需要调试或修改代码：
```bash
# 运行 Web 服务
python -m novel_agent.web.app

# 运行 CLI
python -m novel_agent.main
```

## 📂 项目结构

```
novel_agent/
├── src/
│   └── novel_agent/
│       ├── core/           # 🧠 Core Architecture (Logic/Memory)
│       ├── pipeline/       # ⛓️ Novel Generation Pipeline
│       ├── prompts/        # 📝 System Prompts
│       ├── utils/          # 🛠️ Utility Functions
│       ├── web/            # 🌐 Web Interface (Flask)
│       └── main.py         # 🚀 CLI Entry Point

├── config/                 # ⚙️ Configuration Files
├── projects/               # 📚 User Projects (Auto-generated)
├── docs/                   # 📖 Documentation
└── requirements.txt        # 📦 Dependencies
```

## 🤝 贡献指南
欢迎提交 Issue 和 Pull Request！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 开源协议
本项目采用 [MIT License](LICENSE)。
