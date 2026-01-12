"""
Stage 1: 总纲生成器
生成完整的小说总纲（世界观、主线、人物、卷结构）
"""

from typing import Optional, Dict, Any
from ..core.llm_base import BaseLLMClient, GenerationConfig
from ..core.prompt import PromptManager
from ..core.context import ContextManager


# 默认总纲生成Prompt（当没有定制化Prompt时使用）
DEFAULT_MASTER_OUTLINE_PROMPT = '''# 角色
你是一位资深网文策划，擅长设计能在番茄小说上爆火的小说大纲。

# 核心原则
1. **钩子优先**：从第一章就要有强烈的悬念和冲突
2. **人设鲜明**：主角必须有清晰的动机和成长弧线
3. **节奏紧凑**：每3章一个小高潮，每卷一个大高潮
4. **爽点密集**：扮猪吃虎、打脸反转、实力碾压要有机分布

# 任务
根据用户提供的灵感，生成一份完整的小说总纲。

# 输出格式（严格遵守）

## 一、书名与核心定位
- **书名**：[吸引眼球的书名]
- **一句话卖点**：[核心吸引力]
- **题材标签**：[主标签] / [副标签1] / [副标签2]
- **预估字数**：[总字数目标]

## 二、世界观设定
### 2.1 背景概述
[时代背景、世界运行规则]

### 2.2 力量体系
[等级划分、修炼/升级方式]

### 2.3 核心设定
[本书最独特的创新点]

## 三、主线剧情
### 第一幕：起（第1-XX章）
[开局设定、主角出场、核心冲突建立]

### 第二幕：承（第XX-XX章）
[矛盾升级、能力成长、关键转折]

### 第三幕：转（第XX-XX章）
[危机爆发、真相揭露、高潮对决]

### 第四幕：合（第XX-XX章）
[矛盾解决、新的开始、为续作铺垫/完美收尾]

## 四、核心人物档案
### 主角
- **姓名**：
- **年龄**：
- **身份**：
- **性格**：[外在表现] + [内在动机]
- **金手指**：[核心能力]
- **成长弧线**：[从A到B的转变]

### 女主/重要配角（2-3位）
[同上格式]

### 主要反派
[同上格式]

## 五、卷结构规划
### 第一卷：[卷名]（约XX万字）
- **核心事件**：
- **主角收获**：
- **结尾钩子**：

### 第二卷：[卷名]（约XX万字）
[同上]

（可根据总字数规划更多卷）

## 六、爽点与伏笔布局
### 短线伏笔（3-10章内回收）
- 

### 中线伏笔（一卷内回收）
- 

### 长线伏笔（跨卷回收）
- 

---

# 用户的灵感/想法

{user_input}

{additional_context}
'''


class MasterOutlineGenerator:
    """
    总纲生成器
    
    功能：
    - 根据用户灵感生成完整总纲
    - 支持使用定制化Prompt或默认Prompt
    - 支持迭代修改
    """
    
    def __init__(
        self, 
        llm_client: BaseLLMClient,
        prompt_manager: Optional[PromptManager] = None,
        context_manager: Optional[ContextManager] = None
    ):
        """
        初始化总纲生成器
        
        Args:
            llm_client: LLM客户端
            prompt_manager: Prompt管理器（可选）
            context_manager: 上下文管理器（可选）
        """
        self.llm = llm_client
        self.prompt_manager = prompt_manager
        self.context_manager = context_manager
        
        self.config = GenerationConfig(
            temperature=0.7,
            max_tokens=8192
        )
    
    def generate(
        self, 
        user_input: str,
        custom_prompt_path: Optional[str] = None,
        additional_context: str = ""
    ) -> str:
        """
        生成总纲
        
        Args:
            user_input: 用户的小说灵感/想法
            custom_prompt_path: 定制化Prompt路径（相对于prompts目录）
            additional_context: 额外上下文（如之前的讨论）
            
        Returns:
            str: 生成的总纲内容
        """
        # 尝试加载定制化Prompt
        if custom_prompt_path and self.prompt_manager:
            try:
                prompt_template = self.prompt_manager.load_template(custom_prompt_path)
            except FileNotFoundError:
                prompt_template = DEFAULT_MASTER_OUTLINE_PROMPT
        else:
            prompt_template = DEFAULT_MASTER_OUTLINE_PROMPT
        
        # 构建系统Prompt
        system_prompt = None
        if self.prompt_manager:
            rules = self.prompt_manager.get_system_rules()
            if rules:
                system_prompt = rules
        
        # 渲染Prompt
        prompt = prompt_template.format(
            user_input=user_input,
            additional_context=additional_context
        )
        
        # 调用LLM
        result = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            config=self.config
        )
        
        return result.content
    
    def refine(
        self, 
        current_outline: str, 
        user_feedback: str
    ) -> str:
        """
        根据用户反馈修改总纲
        
        Args:
            current_outline: 当前总纲
            user_feedback: 用户的修改意见
            
        Returns:
            str: 修改后的总纲
        """
        prompt = f'''# 任务
根据用户反馈修改小说总纲。

# 当前总纲
{current_outline}

# 用户反馈
{user_feedback}

# 要求
1. 只修改用户指出的问题
2. 保持整体结构和格式不变
3. 确保修改后的内容逻辑自洽
4. 输出完整的修改后总纲
'''
        
        result = self.llm.generate(prompt, config=self.config)
        return result.content
    
    def expand_section(
        self, 
        outline: str, 
        section_name: str,
        expansion_request: str = ""
    ) -> str:
        """
        扩展总纲的某个部分
        
        Args:
            outline: 当前总纲
            section_name: 要扩展的章节名
            expansion_request: 扩展要求
            
        Returns:
            str: 扩展后的内容
        """
        prompt = f'''# 任务
扩展小说总纲的指定部分，增加更多细节。

# 当前总纲
{outline}

# 需要扩展的部分
{section_name}

# 扩展要求
{expansion_request if expansion_request else "增加更多细节，使其更加具体可执行"}

# 要求
1. 只输出扩展后的该部分内容
2. 保持与总纲其他部分的一致性
3. 增加具体的细节和例子
'''
        
        result = self.llm.generate(prompt, config=self.config)
        return result.content
    
    def save_outline(self, content: str) -> str:
        """
        保存总纲到项目目录
        
        Args:
            content: 总纲内容
            
        Returns:
            str: 保存的文件路径
        """
        if not self.context_manager or not self.context_manager.project_path:
            raise ValueError("没有加载的项目，无法保存")
        
        path = self.context_manager.write_file(content, "master_outline.md")
        
        # 更新项目状态
        self.context_manager.update_stage("master_outline")
        
        return str(path)
