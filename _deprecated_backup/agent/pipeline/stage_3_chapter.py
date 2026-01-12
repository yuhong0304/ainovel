"""
Stage 3: 细纲生成器
将粗纲展开为章节级别的详细大纲（黄金三章结构）
"""

from typing import Optional, List
from ..llm_base import BaseLLMClient, GenerationConfig
from ..prompt_manager import PromptManager
from ..context_manager import ContextManager


DEFAULT_CHAPTER_OUTLINE_PROMPT = '''# 角色
你是一位精通番茄小说节奏的写手，擅长"黄金三章"结构设计。

# 黄金三章法则
每个情节单元（约9000字/3章）必须包含：
- **第1章-铺垫入局**：抛悬念、建期待、主角切入
- **第2章-高潮反转**：视觉奇观、能力展示、爽点爆发
- **第3章-结算迪化**：逻辑闭环、收益可视化、埋下一个钩子

# 任务
将以下剧本粗纲展开为详细的章节细纲。

# 剧本粗纲
{volume_outline}

# 当前要展开的剧本
{current_script}

# 上下文
{context}

# 输出格式

## {script_name} 细纲

**【本组出场人物】**
- **[名字]**: [本组身份/状态] - [核心作用]

**【本组出场道具/设定】**
- **[名称]**: [简述]

---

### 第{start_chapter}章：[小标题]
**【章节定位】**：铺垫入局

**【核心目标】**：[一句话概括]

#### 场景1: [场景名] (0-1000字)
- **地点**：
- **在场人物**：
- **情节要点**：
  1. [具体发生什么]
  2. [关键对话/动作]
- **氛围**：[紧张/轻松/压抑/...]
- **细节点**：[需要着重描写的细节]

#### 场景2: [场景名] (1000-2000字)
[同上结构]

#### 场景3: [场景名] (2000-3000字)
- **...**: ...
- **章末钩子**：[必须是强烈的悬念或危机]

---

### 第{mid_chapter}章：[小标题]
**【章节定位】**：高潮反转

[同上结构，但重点是：]
- 视觉奇观场面
- 爽点爆发
- 反差设计

---

### 第{end_chapter}章：[小标题]
**【章节定位】**：结算迪化

[同上结构，但重点是：]
- 收获结算（能力/物品/关系）
- 伏笔回收或埋设
- 承上启下的钩子

---

## 本组质检清单
- [ ] 每章约3000字，共约9000字
- [ ] 章末都有钩子
- [ ] 有明确的爽点
- [ ] 人设一致性
'''


class ChapterOutlineGenerator:
    """
    细纲生成器
    
    功能：
    - 将剧本粗纲展开为章节细纲
    - 遵循黄金三章结构
    - 确保每章3000字、章末有钩子
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
        volume_outline: str,
        script_name: str,
        start_chapter: int,
        context: str = "",
        custom_prompt_path: Optional[str] = None
    ) -> str:
        """
        生成某个剧本的章节细纲
        
        Args:
            volume_outline: 卷粗纲
            script_name: 剧本名称
            start_chapter: 起始章节号
            context: 上下文（人物状态、前情等）
            custom_prompt_path: 定制Prompt路径
        """
        # 加载Prompt
        if custom_prompt_path and self.prompt_manager:
            try:
                prompt_template = self.prompt_manager.load_template(custom_prompt_path)
            except FileNotFoundError:
                prompt_template = DEFAULT_CHAPTER_OUTLINE_PROMPT
        else:
            prompt_template = DEFAULT_CHAPTER_OUTLINE_PROMPT
        
        # 提取当前剧本内容
        current_script = self._extract_script(volume_outline, script_name)
        
        # 计算章节号
        mid_chapter = start_chapter + 1
        end_chapter = start_chapter + 2
        
        # 获取系统规则
        system_prompt = None
        if self.prompt_manager:
            rules = self.prompt_manager.get_system_rules()
            style = self.prompt_manager.get_writing_style()
            if rules or style:
                system_prompt = f"{rules}\n\n{style}".strip()
        
        # 渲染Prompt
        prompt = prompt_template.format(
            volume_outline=volume_outline,
            current_script=current_script or script_name,
            script_name=script_name,
            start_chapter=start_chapter,
            mid_chapter=mid_chapter,
            end_chapter=end_chapter,
            context=context
        )
        
        result = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            config=self.config
        )
        
        return result.content
    
    def _extract_script(self, outline: str, script_name: str) -> str:
        """从粗纲中提取指定剧本的内容"""
        # 简单的文本提取
        lines = outline.split('\n')
        in_script = False
        script_lines = []
        
        for line in lines:
            if script_name in line and ('剧本' in line or '####' in line):
                in_script = True
            elif in_script and line.startswith('#### 剧本'):
                break
            elif in_script:
                script_lines.append(line)
        
        return '\n'.join(script_lines) if script_lines else ""
    
    def generate_for_volume(
        self,
        volume_outline: str,
        script_count: int = 3,
        start_chapter: int = 1
    ) -> List[str]:
        """
        为整卷生成所有细纲
        
        Args:
            volume_outline: 卷粗纲
            script_count: 剧本数量
            start_chapter: 起始章节号
        """
        outlines = []
        current_chapter = start_chapter
        
        for i in range(1, script_count + 1):
            script_name = f"剧本{i}"
            
            # 添加前情上下文
            context = ""
            if outlines:
                context = f"前一个剧本的结尾：\n{self._get_last_hook(outlines[-1])}"
            
            outline = self.generate(
                volume_outline=volume_outline,
                script_name=script_name,
                start_chapter=current_chapter,
                context=context
            )
            
            outlines.append(outline)
            current_chapter += 3  # 每个剧本3章
        
        return outlines
    
    def _get_last_hook(self, outline: str) -> str:
        """提取细纲最后的钩子"""
        if "章末钩子" in outline:
            idx = outline.rfind("章末钩子")
            return outline[idx:idx+200]
        return ""
    
    def refine(
        self,
        current_outline: str,
        user_feedback: str
    ) -> str:
        """根据反馈修改细纲"""
        prompt = f'''# 任务
根据用户反馈修改章节细纲。

# 当前细纲
{current_outline}

# 用户反馈
{user_feedback}

# 要求
1. 保持黄金三章结构
2. 确保每章约3000字规划
3. 保持章末钩子
4. 输出完整修改后的细纲
'''
        
        result = self.llm.generate(prompt, config=self.config)
        return result.content
    
    def save_outline(
        self, 
        content: str, 
        volume_number: int, 
        script_number: int
    ) -> str:
        """保存细纲"""
        if not self.context_manager or not self.context_manager.project_path:
            raise ValueError("没有加载的项目")
        
        filename = f"v{volume_number:02d}_s{script_number:02d}.md"
        path = self.context_manager.write_file(content, "chapters", filename)
        
        return str(path)
