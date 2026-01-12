"""
Stage 2: 粗纲生成器
将总纲展开为各卷的粗略大纲（剧本结构）
"""

from typing import Optional, List
from ..core.llm_base import BaseLLMClient, GenerationConfig
from ..core.prompt import PromptManager
from ..core.context import ContextManager


DEFAULT_VOLUME_OUTLINE_PROMPT = '''# 角色
你是一位专业的网文编剧，擅长将大纲转化为具体的剧本结构。

# 任务
根据总纲，为第{volume_number}卷生成详细的粗纲（剧本结构）。

# 总纲
{master_outline}

# 输出格式

## 第{volume_number}卷：{volume_title}

### 卷概述
- **核心矛盾**：[本卷主要解决什么问题]
- **主角目标**：[主角想要达成什么]
- **主要障碍**：[阻碍主角的力量]
- **结果收获**：[主角最终获得什么]

### 剧本结构

#### 剧本1: [名称]（第X-X章，约X万字）
**类型**：[主线推进/能力展示/人物塑造/伏笔铺垫]

**起**：
- 场景：[在哪里发生]
- 事件：[发生了什么]
- 钩子：[吸引读者继续的悬念]

**承**：
- 矛盾升级：[冲突如何加剧]
- 主角行动：[主角如何应对]
- 关键转折：[意外发生]

**转**：
- 高潮场面：[最精彩的画面]
- 爽点设计：[读者爽在哪里]
- 反转元素：[有什么出乎意料的]

**合**：
- 结果：[这个剧本的结局]
- 收获：[主角/剧情的推进]
- 下一个钩子：[引向下一个剧本的悬念]

#### 剧本2: [名称]
[同上结构]

（根据卷的字数规划3-5个剧本）

### 本卷伏笔清单
- **埋下**：[本卷埋下的伏笔]
- **回收**：[本卷回收的之前伏笔]

### 本卷人物弧线
- **主角变化**：[从A状态到B状态]
- **关系变化**：[人物关系的演变]

{additional_requirements}
'''


class VolumeOutlineGenerator:
    """
    粗纲生成器
    
    功能：
    - 根据总纲生成各卷的剧本结构
    - 支持逐卷生成或批量生成
    - 确保卷与卷之间的连贯性
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
            temperature=0.7,
            max_tokens=8192
        )
    
    def generate(
        self,
        master_outline: str,
        volume_number: int,
        volume_title: str = "",
        additional_requirements: str = "",
        custom_prompt_path: Optional[str] = None
    ) -> str:
        """
        生成单卷粗纲
        
        Args:
            master_outline: 总纲内容
            volume_number: 卷号
            volume_title: 卷名（可选，从总纲提取）
            additional_requirements: 额外要求
            custom_prompt_path: 定制化Prompt路径
        """
        # 加载Prompt模板
        if custom_prompt_path and self.prompt_manager:
            try:
                prompt_template = self.prompt_manager.load_template(custom_prompt_path)
            except FileNotFoundError:
                prompt_template = DEFAULT_VOLUME_OUTLINE_PROMPT
        else:
            prompt_template = DEFAULT_VOLUME_OUTLINE_PROMPT
        
        # 获取系统规则
        system_prompt = None
        if self.prompt_manager:
            rules = self.prompt_manager.get_system_rules()
            if rules:
                system_prompt = rules
        
        # 渲染Prompt
        prompt = prompt_template.format(
            master_outline=master_outline,
            volume_number=volume_number,
            volume_title=volume_title or f"第{volume_number}卷",
            additional_requirements=additional_requirements
        )
        
        result = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            config=self.config
        )
        
        return result.content
    
    def generate_all(
        self,
        master_outline: str,
        volume_count: int,
        volume_titles: Optional[List[str]] = None
    ) -> List[str]:
        """
        批量生成所有卷的粗纲
        
        Args:
            master_outline: 总纲
            volume_count: 卷数
            volume_titles: 各卷标题（可选）
        """
        outlines = []
        previous_summary = ""
        
        for i in range(1, volume_count + 1):
            title = volume_titles[i-1] if volume_titles and len(volume_titles) >= i else ""
            
            # 添加前情提要，确保连贯
            additional = ""
            if previous_summary:
                additional = f"\n# 前情提要（上一卷结尾）\n{previous_summary}"
            
            outline = self.generate(
                master_outline=master_outline,
                volume_number=i,
                volume_title=title,
                additional_requirements=additional
            )
            
            outlines.append(outline)
            
            # 提取本卷结尾作为下一卷的前情提要
            previous_summary = self._extract_ending(outline)
        
        return outlines
    
    def _extract_ending(self, outline: str) -> str:
        """从粗纲中提取结尾摘要"""
        # 简单提取最后一个剧本的"合"部分
        if "**合**" in outline:
            parts = outline.split("**合**")
            if len(parts) > 1:
                last_part = parts[-1]
                # 取到下一个章节标记或结尾
                end_idx = last_part.find("###")
                if end_idx == -1:
                    end_idx = min(500, len(last_part))
                return last_part[:end_idx].strip()
        return ""
    
    def refine(
        self,
        current_outline: str,
        user_feedback: str,
        master_outline: str = ""
    ) -> str:
        """根据反馈修改粗纲"""
        prompt = f'''# 任务
根据用户反馈修改卷粗纲。

{f"# 总纲参考{chr(10)}{master_outline}" if master_outline else ""}

# 当前粗纲
{current_outline}

# 用户反馈
{user_feedback}

# 要求
1. 只修改用户指出的问题
2. 保持剧本结构完整
3. 确保与总纲一致
4. 输出完整的修改后粗纲
'''
        
        result = self.llm.generate(prompt, config=self.config)
        return result.content
    
    def save_outline(self, content: str, volume_number: int) -> str:
        """保存粗纲"""
        if not self.context_manager or not self.context_manager.project_path:
            raise ValueError("没有加载的项目")
        
        filename = f"volume_{volume_number:02d}.md"
        path = self.context_manager.write_file(content, "volumes", filename)
        
        return str(path)
