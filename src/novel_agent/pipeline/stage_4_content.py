"""
Stage 4: 正文生成器
根据细纲生成约3000字的章节正文
"""

from typing import Optional, Generator
from ..core.llm_base import BaseLLMClient, GenerationConfig
from ..core.prompt import PromptManager
from ..core.context import ContextManager
from ..core.rag import RAGManager
from ..utils import count_words


DEFAULT_CONTENT_PROMPT = '''# 角色
你是一位番茄小说签约作家，擅长写出让读者欲罢不能的网文。

# 核心要求
1. **字数**：本章约3000字（2800-3200字）
2. **节奏**：紧凑不拖沓，每500字左右要有一个小钩子
3. **文风**：口语化、画面感强、少用书面语
4. **钩子**：章末必须有强烈的悬念或危机

# 绝对禁止
- 纯环境描写开篇（必须以人物处境/冲突切入）
- 单双字独立句子
- AI味表达（命运的齿轮、无形的大手）
- 解释性写法（直接展示，不要告诉读者）

# 当前章节细纲
{chapter_outline}

# 上下文
## 前情摘要
{previous_summary}

## 人物状态
{character_status}

## (RAG) 记忆库检索线索
{rag_context}

# 输出要求
直接输出正文内容，不需要标题和其他说明。
开篇直接进入情节，用动作或对话开始。
'''


class ContentGenerator:
    """
    正文生成器 (Intelligent Version)
    
    功能：
    - RAG 增强：自动检索世界观和伏笔
    - 风格自适应：根据章节类型调整参数 (TODO)
    - 自动控制字数
    """
    
    def __init__(
        self,
        llm_client: BaseLLMClient,
        prompt_manager: Optional[PromptManager] = None,
        context_manager: Optional[ContextManager] = None,
        rag_manager: Optional[RAGManager] = None
    ):
        self.llm = llm_client
        self.prompt_manager = prompt_manager
        self.context_manager = context_manager
        self.rag_manager = rag_manager
        
        self.config = GenerationConfig(
            temperature=0.8,
            max_tokens=8192
        )
        
        self.target_words = 3000
        self.word_tolerance = 200
    
    def _retrieve_context(self, query: str) -> str:
        """从RAG检索相关上下文"""
        if not self.rag_manager or not query:
            return ""
        try:
            # 检索最相关的3条设定/旧文
            docs = self.rag_manager.query(query, n_results=3)
            if docs:
                return "\n".join([f"- {d}" for d in docs])
            return ""
        except Exception as e:
            print(f"RAG Retrieval warning: {e}")
            return ""

    def generate(
        self,
        chapter_outline: str,
        previous_summary: str = "",
        character_status: str = "",
        custom_prompt_path: Optional[str] = None
    ) -> str:
        """生成章节正文"""
        # 1. RAG 检索
        rag_context = self._retrieve_context(f"{chapter_outline}\n{previous_summary}")
        
        # 2. 加载 Prompt
        if custom_prompt_path and self.prompt_manager:
            try:
                # 使用 PromptManager 的 render 功能自动注入 rag_context
                # 如果是直接 load_template 则只能拿生文本
                # 这里假设 load_template 返回 raw string
                prompt_template = self.prompt_manager.load_template(custom_prompt_path)
            except FileNotFoundError:
                prompt_template = DEFAULT_CONTENT_PROMPT
        else:
            prompt_template = DEFAULT_CONTENT_PROMPT
        
        # 3. 构建 System Prompt
        system_parts = []
        if self.prompt_manager:
            rules = self.prompt_manager.get_system_rules()
            style = self.prompt_manager.get_writing_style()
            learned = self.prompt_manager.get_learned_rules()
            
            if rules: system_parts.append(rules)
            if style: system_parts.append(style)
            if learned: system_parts.append(f"# 已学习的润色规则\n{learned}")
        
        system_prompt = "\n\n---\n\n".join(system_parts) if system_parts else None
        
        # 4. 渲染 Prompt
        # 检查 prompt_template 是否包含 rag_context 占位符，如果没有但检索到了，强制追加
        prompt = prompt_template
        if "{rag_context}" in prompt:
            prompt = prompt.format(
                chapter_outline=chapter_outline,
                previous_summary=previous_summary or "无",
                character_status=character_status or "参见细纲",
                rag_context=rag_context or "无相关资料"
            )
        else:
            # Fallback formatting
            try:
                prompt = prompt.format(
                    chapter_outline=chapter_outline,
                    previous_summary=previous_summary or "无",
                    character_status=character_status or "参见细纲"
                )
                if rag_context:
                    prompt += f"\n\n# 参考资料 (记忆库)\n{rag_context}"
            except KeyError:
                # 模板可能不包含某些 key，做个保险
                pass

        result = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            config=self.config
        )
        
        return result.content
    
    def generate_stream(
        self,
        chapter_outline: str,
        previous_summary: str = "",
        character_status: str = ""
    ) -> Generator[str, None, None]:
        """流式生成正文"""
        # 1. RAG 检索
        rag_context = self._retrieve_context(f"{chapter_outline}\n{previous_summary}")
        
        # 2. 准备 Prompt
        prompt_template = DEFAULT_CONTENT_PROMPT
        
        system_prompt = None
        if self.prompt_manager:
            rules = self.prompt_manager.get_system_rules()
            style = self.prompt_manager.get_writing_style()
            learned = self.prompt_manager.get_learned_rules()
            parts = [p for p in [rules, style, learned] if p]
            if parts:
                system_prompt = "\n\n".join(parts)
        
        # 3. 渲染
        try:
             prompt = prompt_template.format(
                chapter_outline=chapter_outline,
                previous_summary=previous_summary or "无",
                character_status=character_status or "参见细纲",
                rag_context=rag_context or "暂无检索结果"
            )
        except:
             # Fallback
             prompt = f"细纲: {chapter_outline}\n摘要: {previous_summary}\n参考: {rag_context}"
        
        for chunk in self.llm.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            config=self.config
        ):
            yield chunk
    
    def continue_content(
        self,
        current_content: str,
        chapter_outline: str,
        target_additional_words: int = 1000
    ) -> str:
        """
        续写正文（当字数不足时）
        
        Args:
            current_content: 当前已生成的内容
            chapter_outline: 章节细纲
            target_additional_words: 需要续写的字数
        """
        current_words = count_words(current_content)
        
        prompt = f'''# 任务
续写以下章节内容，再写约{target_additional_words}字。

# 章节细纲
{chapter_outline}

# 当前内容（已有{current_words}字）
{current_content}

# 要求
1. 从当前内容最后自然衔接
2. 保持一致的风格和节奏
3. 如果接近章节结尾，要写出章末钩子
4. 直接输出续写内容，不要重复已有内容
'''
        
        result = self.llm.generate(prompt, config=self.config)
        return current_content + "\n\n" + result.content
    
    def check_and_adjust(
        self,
        content: str,
        chapter_outline: str
    ) -> str:
        """
        检查并调整字数
        
        如果字数不足，自动续写；如果过多，提示截断点
        """
        word_count = count_words(content)
        
        if word_count < self.target_words - self.word_tolerance:
            # 字数不足，续写
            additional_needed = self.target_words - word_count
            return self.continue_content(
                current_content=content,
                chapter_outline=chapter_outline,
                target_additional_words=additional_needed
            )
        elif word_count > self.target_words + self.word_tolerance:
            # 字数过多，提示但不自动截断
            print(f"⚠️ 字数偏多: {word_count}字 (目标: {self.target_words})")
            return content
        else:
            return content
    
    def save_content(
        self,
        content: str,
        chapter_number: int,
        version: str = "raw"  # raw | polished | final
    ) -> str:
        """
        保存正文
        
        Args:
            content: 正文内容
            chapter_number: 章节号
            version: 版本类型
        """
        if not self.context_manager or not self.context_manager.project_path:
            raise ValueError("没有加载的项目")
        
        filename = f"ch{chapter_number:03d}_{version}.md"
        path = self.context_manager.write_file(content, "content", filename)
        
        return str(path)
