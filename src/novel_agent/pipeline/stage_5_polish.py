"""
Stage 5: 润色处理器
对AI生成的正文进行润色，消除AI味
"""

from typing import Optional
from ..core.llm_base import BaseLLMClient, GenerationConfig
from ..core.prompt import PromptManager
from ..core.context import ContextManager


DEFAULT_POLISH_PROMPT = '''# 角色
你是一位资深的网文编辑，专门负责消除AI写作的痕迹，让文字更像人写的。

# 润色原则

## 必须修改
1. **开篇问题**：如果以纯环境描写开篇，改为人物处境/动作切入
2. **超短句**：所有1-2字的独立句子，扩展为3字以上
3. **AI烂梗**：
   - "命运的齿轮" → 删除或具体化
   - "瞳孔猛缩" → 改为动作僵硬/呼吸停滞
   - "肾上腺素飙升" → 改为心跳/具体感官
   - "无形的大手" → 改为具体物理感受
4. **被动语态**："被XX" → 主动表达
5. **解释性写法**："他感到害怕" → 展示害怕的生理反应

## 需要增强
1. **口语化**：书面表达 → 更接地气的说法
2. **生活颗粒**：在紧张场景中加入无关紧要的小细节
3. **主观视角**：客观陈述 → 通过角色感官过滤
4. **动作颗粒度**：笼统动作 → 2-3个具体生理细节

## 禁止过度修改
- 不要改变剧情走向
- 不要增删主要内容
- 保持原有的节奏感

# 原文
{original_content}

# 输出要求
直接输出润色后的完整正文，不需要解释修改了什么。
'''


class PolishProcessor:
    """
    润色处理器
    
    功能：
    - 消除AI味
    - 应用写作规范
    - 应用学习到的规则
    """
    
    def __init__(
        self,
        llm_client: BaseLLMClient,
        prompt_manager: Optional[PromptManager] = None,
        context_manager: Optional[ContextManager] = None
    ):
        self.llm = llm_client
        self.prompt_manager = prompt_manager
        self.context_manager = context_manager
        
        self.config = GenerationConfig(
            temperature=0.5,  # 较低温度，减少发挥
            max_tokens=8192
        )
    
    def polish(
        self,
        content: str,
        custom_prompt_path: Optional[str] = None
    ) -> str:
        """
        润色正文
        
        Args:
            content: 原始正文
            custom_prompt_path: 定制Prompt路径
        """
        # 加载Prompt
        if custom_prompt_path and self.prompt_manager:
            try:
                prompt_template = self.prompt_manager.load_template(custom_prompt_path)
            except FileNotFoundError:
                prompt_template = DEFAULT_POLISH_PROMPT
        else:
            prompt_template = DEFAULT_POLISH_PROMPT
        
        # 构建系统Prompt（包含学习到的规则）
        system_parts = []
        if self.prompt_manager:
            style = self.prompt_manager.get_writing_style()
            learned = self.prompt_manager.get_learned_rules(force_reload=True)
            
            if style:
                system_parts.append(f"# 文字规范\n{style}")
            if learned:
                system_parts.append(f"# 从人工修改中学习到的规则（优先级最高）\n{learned}")
        
        system_prompt = "\n\n---\n\n".join(system_parts) if system_parts else None
        
        # 渲染Prompt
        prompt = prompt_template.format(original_content=content)
        
        result = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            config=self.config
        )
        
        return result.content
    
    def polish_section(
        self,
        content: str,
        section_start: int,
        section_end: int,
        specific_issues: str = ""
    ) -> str:
        """
        润色特定段落
        
        Args:
            content: 完整正文
            section_start: 起始行号
            section_end: 结束行号
            specific_issues: 具体问题描述
        """
        lines = content.split('\n')
        section = '\n'.join(lines[section_start:section_end])
        
        prompt = f'''# 任务
润色以下段落，解决指定问题。

# 段落内容
{section}

# 需要解决的问题
{specific_issues if specific_issues else "消除AI味，让文字更自然"}

# 要求
只输出润色后的段落，不要输出其他内容。
'''
        
        result = self.llm.generate(prompt, config=self.config)
        
        # 替换原段落
        lines[section_start:section_end] = result.content.split('\n')
        return '\n'.join(lines)
    
    def batch_polish(
        self,
        content: str,
        chunk_size: int = 1500
    ) -> str:
        """
        分段润色（适用于长文本）
        
        Args:
            content: 完整正文
            chunk_size: 每段字数
        """
        paragraphs = content.split('\n\n')
        polished_parts = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_size + para_size > chunk_size and current_chunk:
                # 润色当前块
                chunk_text = '\n\n'.join(current_chunk)
                polished = self.polish(chunk_text)
                polished_parts.append(polished)
                
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # 处理最后一块
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            polished = self.polish(chunk_text)
            polished_parts.append(polished)
        
        return '\n\n'.join(polished_parts)
    
    def save_versions(
        self,
        raw_content: str,
        polished_content: str,
        chapter_number: int
    ) -> dict:
        """
        保存原始版和润色版
        
        Args:
            raw_content: 原始正文
            polished_content: 润色后正文
            chapter_number: 章节号
            
        Returns:
            dict: 文件路径
        """
        if not self.context_manager or not self.context_manager.project_path:
            raise ValueError("没有加载的项目")
        
        raw_path = self.context_manager.write_file(
            raw_content, 
            "content", 
            f"ch{chapter_number:03d}_raw.md"
        )
        
        polished_path = self.context_manager.write_file(
            polished_content,
            "content",
            f"ch{chapter_number:03d}_polished.md"
        )
        
        return {
            "raw": str(raw_path),
            "polished": str(polished_path)
        }
