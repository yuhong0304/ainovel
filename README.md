# 📚 Novel Agent (番茄小说/网文 AI 助手)

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/version-1.1.0-brightgreen.svg" alt="Version">
  <img src="https://img.shields.io/badge/LLM-Gemini%203.0%20|%20GPT--5%20|%20Claude%204-orange.svg" alt="LLM">
</p>

<p align="center">
  <b>🚀 一键生成网文 | 🧠 AI 真正记得你的设定 | 💻 Web界面开箱即用</b>
</p>

---

## 🎯 这是什么？

**Novel Agent** 是一个基于 AI 的半自动化网文创作系统。它能帮你：

- 📝 从一句话灵感生成完整的小说大纲
- 🧠 使用 RAG 技术让 AI 记住你所有的人物设定和世界观
- ✨ 一键生成正文，支持批量创作
- 📤 导出为 TXT / DOCX / EPUB 格式

**支持的 AI 模型** (2026年1月)：
- Google Gemini 3.0 Pro / Flash
- OpenAI GPT-5 / GPT-4o
- Anthropic Claude Opus 4.5 / Sonnet 4.5

---

## ⚡ 30秒快速开始

### Windows 用户

```
1. 双击 install.bat   ← 自动安装依赖
2. 编辑 .env 文件，填入 API Key
3. 双击 start.bat     ← 启动程序
```

### Linux / Mac 用户

```bash
chmod +x install.sh start.sh
./install.sh          # 安装依赖
nano .env             # 编辑配置
./start.sh            # 启动程序
```

---

## ✨ 核心功能

### 🚀 完整创作流水线

```
灵感 → 元提示生成 → 总纲 → 卷纲 → 章节大纲 → 正文 → 润色
```

每个阶段都可以人工审核和修改，AI 会根据你的修改学习你的写作风格。

### 🧠 RAG 记忆系统

使用 ChromaDB 向量数据库，让 AI 真正"读懂"你的设定：

- 人物小传自动索引
- 世界观设定随时检索
- 写到第100章，AI 依然记得第1章的伏笔

### 🎭 世界书管理

**Web 界面操作**：
- 在 `🌍 世界书` 标签页中可视化的管理角色、地点和设定。
- 支持创建、编辑、删除卡片。
- 卡片内容会自动进入 RAG 索引，被 AI 在写作时引用。

### 📤 多格式导出

**Web 界面操作**：
- 在 `📤 导出` 标签页一键下载。
- 支持 **TXT** (纯文本)、**Word** (DOCX) 和 **EPUB** (电子书) 格式。

### 📊 批量生成

**Web 界面操作**：
- 在 `⚡ 批量生成` 标签页配置任务。
- 支持设定起始/结束章节和标题。
- 实时查看生成进度和日志，支持后台运行。

### 🔄 版本管理

**Web 界面操作**：
- 在 `🕰️ 版本历史` 标签页查看文件的修改记录。
- 自动保存每次生成和编辑的内容。
- 支持一键回滚到任意历史版本，并在回滚前自动备份当前内容。

---

## 📂 项目结构

```
novel-agent/
├── 📦 src/novel_agent/      # 源代码
│   ├── core/                # 核心模块 (LLM客户端/RAG/配置)
│   ├── pipeline/            # 生成流水线
│   ├── prompts/             # Prompt模板
│   ├── utils/               # 工具 (导出/批量/世界书/版本)
│   └── web/                 # Web界面
│
├── 🧪 tests/                # 测试文件
├── 📚 projects/             # 你的小说项目 (自动创建)
│
├── 📄 install.bat           # Windows 一键安装
├── 📄 start.bat             # Windows 启动器
├── 📄 install.sh            # Linux/Mac 安装
├── 📄 start.sh              # Linux/Mac 启动器
│
├── ⚙️ config.yaml           # 配置文件
├── 🔒 .env.example          # 环境变量模板
└── 📖 README.md             # 本文件
```

---

## ⚙️ 配置说明

### 环境变量 (.env)

```ini
# 必填 - 至少配置一个 API Key
GEMINI_API_KEY=your_key_here      # Google Gemini (推荐)
OPENAI_API_KEY=your_key_here      # OpenAI GPT
ANTHROPIC_API_KEY=your_key_here   # Anthropic Claude

# 可选配置
GEMINI_MODEL=gemini-2.5-flash     # 默认模型
WEB_PORT=5000                      # Web服务端口
```

### 获取 API Key

| 提供商 | 获取地址 | 推荐模型 |
|--------|----------|----------|
| Google Gemini | [aistudio.google.com](https://aistudio.google.com/app/apikey) | gemini-2.5-flash |
| OpenAI | [platform.openai.com](https://platform.openai.com/api-keys) | gpt-4o |
| Anthropic | [console.anthropic.com](https://console.anthropic.com/) | claude-sonnet-4.5 |

---

## 🔧 开发者指南

### 安装开发依赖

```bash
pip install -e ".[dev]"      # 开发工具
pip install -e ".[export]"   # 导出功能
pip install -e ".[openai]"   # OpenAI支持
pip install -e ".[claude]"   # Claude支持
pip install -e ".[full]"     # 全部功能
```

### 运行测试

```bash
pytest tests/ -v
```

### 代码检查

```bash
ruff check src/
mypy src/novel_agent
```

---

## 📋 版本历史

### v1.1.0 (2026-01-13)
- ✨ 新增导出功能 (TXT/DOCX/EPUB)
- ✨ 新增批量生成模块
- ✨ 新增世界书/角色卡片管理
- ✨ 新增版本历史管理
- ✨ 新增多模型支持 (OpenAI, Claude)
- 🔧 更新模型到 2026 最新版本

### v1.0.0 (2026-01-12)
- 🚀 首次发布
- 完整的创作流水线
- RAG 记忆系统
- Web UI 和 CLI

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 开源协议

[MIT License](LICENSE) © 2026 yuhong

---

<p align="center">
  <b>⭐ 如果这个项目对你有帮助，请给个 Star！</b>
</p>
