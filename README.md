# 📚 Novel Agent (番茄小说/网文 AI 助手)

> 一个基于 Gemini API 和 ChromaDB 的半自动化网文创作系统。
> 从灵感到大纲，从大纲到正文，全程 RAG (检索增强生成) 辅助，让 AI 真正读懂你的设定。

<p align="center">
  <a href="https://github.com/yuhong0304/ainovel/actions/workflows/ci.yml">
    <img src="https://github.com/yuhong0304/ainovel/actions/workflows/ci.yml/badge.svg" alt="CI Status">
  </a>
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/LLM-Gemini%202.0-orange.svg" alt="Gemini">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  </a>
  <img src="https://img.shields.io/badge/version-1.1.0-brightgreen.svg" alt="Version">
</p>

---

## ✨ 核心特性

| 功能 | 描述 |
|------|------|
| 🚀 **完整流水线** | 灵感 → 总纲 → 卷纲 → 章纲 → 正文 → 润色，全流程覆盖 |
| 🧠 **真实记忆 (RAG)** | 使用 ChromaDB 向量数据库，自动索引人物小传、世界观设定，AI 写第100章时依然记得第1章的伏笔 |
| 💻 **Web UI** | 全功能 Web 界面，支持分屏写作、状态监控、一键生成 |
| 🖥️ **CLI 模式** | 命令行交互，适合高效工作流 |
| 📝 **元提示生成** | 根据灵感自动生成定制化系统提示词 |
| ✨ **智能润色** | AI 辅助润色，从人工修改中学习你的写作风格 |
| 📤 **多格式导出** | 支持 TXT/DOCX/EPUB 格式导出 |
| 🎭 **世界书管理** | 角色卡片、地点设定、势力关系一键管理 |
| 🤖 **多模型支持** | Gemini / OpenAI GPT-4 / Claude 自由切换 |

## 🛠️ 快速开始

### 环境要求

- Python 3.9+
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### 安装

```bash
# 克隆项目
git clone https://github.com/yuhong0304/ainovel.git
cd ainovel

# 创建虚拟环境 (推荐)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装
pip install -e .

# 安装可选功能
pip install -e ".[export]"   # 导出功能 (DOCX/EPUB)
pip install -e ".[openai]"   # OpenAI GPT-4 支持
pip install -e ".[claude]"   # Anthropic Claude 支持
pip install -e ".[all]"      # 所有额外功能
```

### 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，填入你的 API Key
GEMINI_API_KEY=your_api_key_here
```

### 运行

```bash
# 启动 Web 界面 (推荐)
novel-web
# 浏览器访问 http://localhost:5000

# 或使用命令行模式
novel-agent
```

## 📂 项目结构

```
ainovel/
├── src/novel_agent/        # 📦 源代码
│   ├── core/               # 🧠 核心模块 (配置/上下文/LLM/RAG)
│   ├── pipeline/           # ⛓️ 生成流水线
│   ├── prompts/            # 📝 提示词模板
│   ├── utils/              # 🛠️ 工具函数 (导出/批量/统计)
│   ├── web/                # 🌐 Web 界面
│   └── main.py             # 🚀 CLI 入口
├── tests/                  # 🧪 测试
├── docs/                   # 📖 文档
├── config.yaml             # ⚙️ 配置文件
└── projects/               # 📚 用户项目 (自动生成)
```

## 🔧 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check src/

# 类型检查
mypy src/novel_agent

# 安装 pre-commit hooks
pre-commit install
```

## 📋 路线图

- [x] 基础生成流水线
- [x] RAG 记忆系统
- [x] Web UI
- [x] 多格式导出 (TXT/DOCX/EPUB)
- [x] 多模型支持 (OpenAI, Claude)
- [x] 世界书/角色卡片管理
- [x] 版本历史管理
- [ ] 插件系统
- [ ] 在线协作

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 开源协议

[MIT License](LICENSE) © 2026 yuhong
