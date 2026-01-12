"""
Stage 0: 元提示生成器
根据小说类型/灵感自动生成定制化的系统prompt和各阶段prompt
参考知名网文作家的写作结构设计
"""

from typing import Dict, Optional, Any
from ..core.llm_base import BaseLLMClient, GenerationConfig


# 元提示：用于生成适配任意小说的定制化prompt
META_PROMPT_TEMPLATE = '''# 你是一位顶级网文策划专家

你需要根据用户提供的小说灵感，生成一套完整的**定制化写作规范**。

## 你的知识背景

你精通以下大神作家的写作技法：
- **猫腻**（《庆余年》《将夜》）：宏大世界观构建、伏笔回收、人物成长弧线
- **烽火戏诸侯**（《雪中悍刀行》《剑来》）：诗意文笔、江湖气质、细腻情感
- **辰东**（《遮天》《完美世界》）：热血战斗、爽点密集、金句频出
- **天蚕土豆**（《斗破苍穹》《武动乾坤》）：节奏明快、升级体系、少年热血
- **爱潜水的乌贼**（《诡秘之主》）：规则体系、悬疑解谜、人设立体
- **老鹰吃小鸡**（《全球高武》）：数据流、系统流、合理金手指
- **会说话的肘子**（《大王饶命》）：吐槽搞笑、轻松日常、爽点设计

## 任务

根据用户输入的小说灵感，分析最适合的写作风格组合，然后生成以下内容：

### 输出格式（严格遵守）

```yaml
# 小说定制化配置

## 1. 核心定位
书名建议: [3个备选]
题材标签: [主标签, 副标签1, 副标签2]
目标读者: [画像描述]
核心卖点: [一句话总结，必须抓人]
对标作品: [2-3部类似成功作品]

## 2. 风格参数
基调: [热血/轻松/黑暗/治愈/悬疑/...]
节奏: [快节奏爽文/中速稳健/慢热厚重]
爽点密度: [每章X个/平均X字一个]
虐点容忍度: [低/中/高] 
幽默成分: [无/点缀/主调]

## 3. 世界观框架
背景类型: [现代/古代/末世/玄幻/科幻/...]
力量体系: [简述等级/规则]
独特设定: [本书最核心的创新点]

## 4. 人物模板
主角人设关键词: [3-5个词]
主角金手指: [核心能力/系统]
主角性格公式: [外在表现 + 内在动机]
适合的配角类型: [列举3-5类]

## 5. 节奏公式
开篇策略: [如何在前3章抓住读者]
章末钩子: [本书适合的钩子类型]
高潮布局: [每X章需要一个大爽点]
伏笔建议: [短线/中线/长线如何布置]

## 6. 禁忌清单
绝对禁止: [针对本类型的雷点]
慎用元素: [容易写崩的地方]
```

---

## 用户输入的小说灵感

{user_inspiration}
'''


# 系统Prompt生成模板
SYSTEM_PROMPT_GENERATOR = '''# 根据定制化配置生成系统Prompt

你需要将以下小说配置转化为一份**完整的系统级写作规范**。

这份规范将作为AI写作的核心指导，必须：
1. 具体可执行（不能太抽象）
2. 包含正反例子
3. 针对该小说的特点定制

---

## 小说配置

{novel_config}

---

## 输出格式

生成一份Markdown格式的系统Prompt，包含以下章节：

# [书名] 写作规范

## 一、核心卖点与调性
[明确本书最核心的吸引力是什么]

## 二、节奏与爽点公式
[具体的章节节奏要求]
[爽点设计规范]
[钩子设计规范]

## 三、人物执行标准
### 主角
[详细的主角行为准则]
### 配角规范
[各类配角的写作要点]

## 四、文风要求
[叙事风格]
[对话风格]
[战斗/情感/日常场景的写法]

## 五、禁忌清单
[具体的禁止事项]
[每条配示例]

## 六、本书特色元素
[需要反复强化的特色]
'''


# 阶段Prompt生成模板
STAGE_PROMPT_GENERATOR = '''# 根据定制化配置生成阶段Prompt

你需要将小说配置转化为**各阶段专用的Prompt模板**。

---

## 小说配置

{novel_config}

---

## 需要生成的阶段Prompt

### 1. 总纲生成Prompt (master_outline.md)
用于生成完整的小说总纲，包含世界观、主线、人物档案、卷结构。
要求：符合本书的风格定位，参考成功作品的结构。

### 2. 粗纲生成Prompt (volume_outline.md)  
用于将卷大纲细化为剧本结构（矛盾-高潮-解决）。
要求：符合本书的节奏公式。

### 3. 细纲生成Prompt (chapter_outline.md)
用于将剧本细化为章节大纲（每章3000字）。
要求：包含章末钩子设计。

### 4. 正文生成Prompt (content_write.md)
用于根据细纲生成正文。
要求：符合本书的文风要求。

### 5. 润色Prompt (polish.md)
用于润色正文，消除AI味。
要求：针对本书风格优化。

---

## 输出格式

为每个阶段生成独立的Prompt，用分隔线隔开：

===== master_outline.md =====
[Prompt内容]

===== volume_outline.md =====
[Prompt内容]

（以此类推）
'''


class MetaPromptGenerator:
    """
    元提示生成器
    
    功能：
    - 根据用户输入的小说灵感，分析适合的写作风格
    - 生成定制化的系统Prompt和各阶段Prompt
    - 保存配置供后续使用
    """
    
    def __init__(self, llm_client: BaseLLMClient):
        """
        初始化元提示生成器
        
        Args:
            llm_client: LLM客户端实例
        """
        self.llm = llm_client
        self.config = GenerationConfig(
            temperature=0.8,  # 略高创意度
            max_tokens=8192
        )
    
    def analyze_inspiration(self, inspiration: str) -> str:
        """
        分析用户灵感，生成小说定制化配置
        
        Args:
            inspiration: 用户输入的小说灵感/想法
            
        Returns:
            str: YAML格式的定制化配置
        """
        prompt = META_PROMPT_TEMPLATE.format(user_inspiration=inspiration)
        result = self.llm.generate(prompt, config=self.config)
        return result.content
    
    def generate_system_prompt(self, novel_config: str) -> str:
        """
        根据配置生成系统级Prompt
        
        Args:
            novel_config: 小说定制化配置
            
        Returns:
            str: 系统Prompt内容
        """
        prompt = SYSTEM_PROMPT_GENERATOR.format(novel_config=novel_config)
        result = self.llm.generate(prompt, config=self.config)
        return result.content
    
    def generate_stage_prompts(self, novel_config: str) -> Dict[str, str]:
        """
        根据配置生成各阶段Prompt
        
        Args:
            novel_config: 小说定制化配置
            
        Returns:
            Dict[str, str]: 阶段名 -> Prompt内容
        """
        prompt = STAGE_PROMPT_GENERATOR.format(novel_config=novel_config)
        result = self.llm.generate(prompt, config=self.config)
        
        # 解析输出，拆分为各阶段
        stages = {}
        content = result.content
        
        stage_markers = [
            ("master_outline.md", "volume_outline.md"),
            ("volume_outline.md", "chapter_outline.md"),
            ("chapter_outline.md", "content_write.md"),
            ("content_write.md", "polish.md"),
            ("polish.md", None)
        ]
        
        for current, next_stage in stage_markers:
            start_marker = f"===== {current} ====="
            if start_marker in content:
                start_idx = content.index(start_marker) + len(start_marker)
                if next_stage:
                    end_marker = f"===== {next_stage} ====="
                    if end_marker in content:
                        end_idx = content.index(end_marker)
                    else:
                        end_idx = len(content)
                else:
                    end_idx = len(content)
                
                stage_content = content[start_idx:end_idx].strip()
                stages[current] = stage_content
        
        return stages
    
    def initialize_novel(
        self, 
        inspiration: str,
        prompts_dir: str,
        project_name: str
    ) -> Dict[str, Any]:
        """
        完整初始化流程：从灵感到所有Prompt
        
        Args:
            inspiration: 用户输入的小说灵感
            prompts_dir: prompts目录路径
            project_name: 项目名称
            
        Returns:
            Dict: 包含所有生成结果的字典
        """
        from pathlib import Path
        
        prompts_path = Path(prompts_dir)
        project_prompts = prompts_path / "projects" / project_name
        project_prompts.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # Step 1: 分析灵感，生成配置
        print("📊 正在分析小说灵感...")
        novel_config = self.analyze_inspiration(inspiration)
        results["config"] = novel_config
        
        # 保存配置
        config_path = project_prompts / "novel_config.yaml"
        config_path.write_text(novel_config, encoding="utf-8")
        print(f"✅ 配置已保存: {config_path}")
        
        # Step 2: 生成系统Prompt
        print("📝 正在生成系统Prompt...")
        system_prompt = self.generate_system_prompt(novel_config)
        results["system_prompt"] = system_prompt
        
        # 保存系统Prompt
        system_path = project_prompts / "system_prompt.md"
        system_path.write_text(system_prompt, encoding="utf-8")
        print(f"✅ 系统Prompt已保存: {system_path}")
        
        # Step 3: 生成各阶段Prompt
        print("📝 正在生成阶段Prompt...")
        stage_prompts = self.generate_stage_prompts(novel_config)
        results["stage_prompts"] = stage_prompts
        
        # 保存各阶段Prompt
        stages_dir = project_prompts / "stages"
        stages_dir.mkdir(exist_ok=True)
        for stage_name, content in stage_prompts.items():
            stage_path = stages_dir / stage_name
            stage_path.write_text(content, encoding="utf-8")
            print(f"✅ {stage_name} 已保存")
        
        print("\n🎉 小说初始化完成！")
        return results
    
    def refine_config(
        self, 
        current_config: str, 
        user_feedback: str
    ) -> str:
        """
        根据用户反馈优化配置
        
        Args:
            current_config: 当前配置
            user_feedback: 用户的修改意见
            
        Returns:
            str: 优化后的配置
        """
        prompt = f'''# 根据用户反馈优化配置

## 当前配置
{current_config}

## 用户反馈
{user_feedback}

## 任务
根据用户反馈修改配置，保持YAML格式不变，只修改需要调整的部分。
输出完整的修改后配置。
'''
        result = self.llm.generate(prompt, config=self.config)
        return result.content
