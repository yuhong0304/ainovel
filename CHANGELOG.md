# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 更多测试用例
- 文档完善

---

## [1.1.0] - 2026-01-13

### Added
- 🚀 **导出功能**: 支持导出为 TXT/DOCX/EPUB 格式
- 📚 **批量生成**: 一键生成多章内容，支持断点续传
- 🎭 **角色/世界观卡片**: 完整的世界书管理系统，自动索引到 RAG
- 🔄 **版本管理**: 内容版本历史，支持对比和回滚
- 📊 **统计仪表板**: 字数统计、成本追踪、生成趋势
- 🤖 **多模型支持**: 新增 OpenAI GPT-4 和 Anthropic Claude 支持
- 📝 **章节大纲生成器**: 更细粒度的章节规划

### Changed
- 优化 `pyproject.toml` 配置，添加可选依赖组
- 改进 CI/CD 流程，增加包验证步骤

### Technical
- 新增模块: `utils/exporter.py`, `utils/batch.py`, `utils/worldbook.py`
- 新增模块: `utils/versioning.py`, `utils/stats.py`
- 新增模块: `core/multi_llm.py`, `pipeline/chapter_outliner.py`

---

## [1.0.0] - 2026-01-13

### Added
- 🚀 **完整的小说生成流水线**: 灵感 → 总纲 → 卷纲 → 章纲 → 正文 → 润色
- 🧠 **RAG 记忆系统**: 基于 ChromaDB 的向量数据库，支持人物小传、世界观设定检索
- 💻 **Web UI**: 全功能 Web 界面，支持分屏写作和实时预览
- 🖥️ **CLI 模式**: 命令行交互界面
- 📝 **元提示生成**: 根据灵感自动生成定制化系统提示词
- 📚 **多项目管理**: 支持同时管理多个小说项目
- ✨ **润色功能**: AI 辅助润色，支持分段处理
- 📖 **规则学习**: 从人工修改中学习写作规则
- 🧪 **测试套件**: pytest 测试框架
- 🔧 **开发工具**: ruff, mypy, pre-commit 配置
- 🚀 **CI/CD**: GitHub Actions 自动化测试和发布

### Technical
- 采用标准 `src/` 项目布局
- 支持 Python 3.9+
- 使用 `setuptools` 构建
- GitHub Actions CI/CD 流程

---

## [0.1.0] - 2026-01-12

### Added
- 初始项目结构
- 基础 LLM 客户端实现
- 基础 Prompt 管理

[Unreleased]: https://github.com/yuhong0304/ainovel/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/yuhong0304/ainovel/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/yuhong0304/ainovel/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/yuhong0304/ainovel/releases/tag/v0.1.0
