"""
章节大纲生成器
生成更细粒度的章节大纲
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChapterOutline:
    """章节大纲"""
    chapter_num: int
    title: str
    summary: str
    key_events: List[str]
    characters_involved: List[str]
    emotions: List[str]
    word_target: int = 3000
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "chapter_num": self.chapter_num,
            "title": self.title,
            "summary": self.summary,
            "key_events": self.key_events,
            "characters_involved": self.characters_involved,
            "emotions": self.emotions,
            "word_target": self.word_target,
            "notes": self.notes
        }
    
    def to_prompt_context(self) -> str:
        """转换为prompt上下文"""
        lines = [
            f"## 第{self.chapter_num}章：{self.title}",
            f"**概要**: {self.summary}",
            f"**主要事件**: {'; '.join(self.key_events)}",
            f"**涉及角色**: {', '.join(self.characters_involved)}",
            f"**情感基调**: {', '.join(self.emotions)}",
            f"**目标字数**: {self.word_target}字",
        ]
        if self.notes:
            lines.append(f"**备注**: {self.notes}")
        return "\n".join(lines)


class ChapterOutlineGenerator:
    """
    章节大纲生成器
    
    功能:
    - 从卷纲生成详细章节大纲
    - 支持自动拆分场景
    - 情感曲线规划
    """
    
    PROMPT_TEMPLATE = """你是一位专业的网文策划编辑。请根据以下卷纲内容，生成更详细的章节大纲。

## 卷纲概要
{volume_outline}

## 当前需要展开的章节
{chapter_range}

## 输出要求
请为每个章节生成：
1. 章节标题（吸引眼球，有悬念）
2. 内容概要（100-150字）
3. 关键事件（3-5个要点）
4. 涉及角色
5. 情感基调（如：紧张、温馨、热血、悬疑等）
6. 特别注意事项

## 格式要求
请用以下 JSON 格式输出:
```json
[
  {{
    "chapter_num": 1,
    "title": "章节标题",
    "summary": "章节概要...",
    "key_events": ["事件1", "事件2", "事件3"],
    "characters_involved": ["角色1", "角色2"],
    "emotions": ["紧张", "期待"],
    "notes": "特别注意事项"
  }}
]
```
"""

    def __init__(self, llm_client, prompt_manager=None):
        """
        初始化生成器
        
        Args:
            llm_client: LLM客户端
            prompt_manager: Prompt管理器（可选）
        """
        self.llm = llm_client
        self.prompt_manager = prompt_manager
    
    def generate_outlines(
        self,
        volume_outline: str,
        start_chapter: int,
        end_chapter: int,
        context: str = ""
    ) -> List[ChapterOutline]:
        """
        生成章节大纲
        
        Args:
            volume_outline: 卷纲内容
            start_chapter: 起始章节号
            end_chapter: 结束章节号
            context: 额外上下文
        """
        chapter_range = f"第{start_chapter}章 至 第{end_chapter}章"
        
        prompt = self.PROMPT_TEMPLATE.format(
            volume_outline=volume_outline,
            chapter_range=chapter_range
        )
        
        if context:
            prompt += f"\n\n## 额外上下文\n{context}"
        
        try:
            result = self.llm.generate(prompt)
            outlines = self._parse_outlines(result.text)
            return outlines
        except Exception as e:
            logger.error(f"生成章节大纲失败: {e}")
            raise
    
    def _parse_outlines(self, response: str) -> List[ChapterOutline]:
        """解析LLM响应为章节大纲列表"""
        import json
        import re
        
        # 尝试提取 JSON
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析
            json_str = response
        
        try:
            data = json.loads(json_str)
            outlines = []
            
            for item in data:
                outline = ChapterOutline(
                    chapter_num=item.get("chapter_num", 0),
                    title=item.get("title", ""),
                    summary=item.get("summary", ""),
                    key_events=item.get("key_events", []),
                    characters_involved=item.get("characters_involved", []),
                    emotions=item.get("emotions", []),
                    word_target=item.get("word_target", 3000),
                    notes=item.get("notes", "")
                )
                outlines.append(outline)
            
            return outlines
            
        except json.JSONDecodeError as e:
            logger.error(f"解析章节大纲JSON失败: {e}")
            # 返回空列表或尝试其他解析方式
            return []
    
    def expand_single_chapter(
        self,
        chapter_outline: ChapterOutline,
        detail_level: str = "medium"
    ) -> str:
        """
        展开单个章节为更详细的scene breakdown
        
        Args:
            chapter_outline: 章节大纲
            detail_level: 详细程度 (low, medium, high)
        """
        prompt = f"""请将以下章节大纲展开为详细的场景分解：

{chapter_outline.to_prompt_context()}

## 要求
- 将章节分解为3-5个场景
- 每个场景包含：地点、参与角色、发生的事、对话要点、情感变化
- 详细程度：{detail_level}

## 输出格式
### 场景1: [场景名称]
- **地点**: ...
- **角色**: ...
- **内容**: ...
- **对话要点**: ...
- **情感**: ...

[继续其他场景]
"""
        
        result = self.llm.generate(prompt)
        return result.text
