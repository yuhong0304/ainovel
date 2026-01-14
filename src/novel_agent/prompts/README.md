# Prompt 体系文档

## 目录结构

- **system/**: 系统级 Prompt，定义核心规则和风格
    - `core_rules.md`: 绝对红线与核心执行策略
    - `writing_style.md`: 具体的文风指导（SHOW, DON'T TELL）
    - `learning_prompt.md`: 用于 RuleLearner 提取规则的 Prompt
- **stages/**: 流程阶段 Prompt
    - `meta.py` (Stage 0): 灵感生成 (Code-based)
    - `master_outline.md`: 总纲生成
    - `volume_outline.md`: 卷纲生成
    - `chapter_outline.md`: 章纲生成
    - `content_write.md`: 正文生成 (默认通用模板)
    - `polish.md`: 润色优化
    - **content_variants/**: 场景化正文变体
        - `action.md`: 战斗/高体能耗场景
        - `emotional.md`: 情感/日常/心理流场景
        - `suspense.md`: 悬疑/恐怖/探索场景
- **projects/**: 项目专属 Prompt (自动生成)
    - `[project_name]/system_prompt.md`: 项目特定的世界观和设定注入
- **learned/**: 自动学习规则库
    - `polish_rules.md`: RuleLearner 自动追加的规则

## 使用说明

### ContentGenerator
`ContentGenerator` 会自动组合以下部分：
1. `system/core_rules.md`
2. `system/writing_style.md`
3. `learned/polish_rules.md`
4. `[Project System Prompt]` (可选)
5. `stages/content_write.md` (或 `content_variants/*.md`)

### RAG 注入
所有 `content` 相关的模板都支持 `{rag_context}` 占位符，用于注入从 Worldbook 检索到的相关设定。
