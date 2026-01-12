"""
Stage 6: 规则学习器
通过对比润色版和人工修改版，自动学习新的润色规则
"""

import re
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path
from ..llm_base import BaseLLMClient, GenerationConfig
from ..prompt_manager import PromptManager
from ..context_manager import ContextManager


DIFF_ANALYSIS_PROMPT = '''# 角色
你是一位写作规范分析专家，擅长从人工修改中提取写作规则。

# 任务
对比以下两个版本的文本，分析人工进行了哪些修改，并提取可复用的写作规则。

# AI润色版
{polished_version}

# 人工最终版
{final_version}

# 分析要求
1. 找出所有有意义的修改（忽略标点符号等微小调整）
2. 分析每个修改背后的规律
3. 将规律抽象为可复用的规则

# 输出格式（严格遵守）

## 规则 #{rule_number} ({date})
- **原文**: [修改前的文本片段]
- **修改**: [修改后的文本片段]
- **规则**: [抽象出的可复用规则，一句话描述]
- **适用场景**: [什么情况下应用此规则]

（如有多条规则，继续列出）

如果没有发现有意义的修改，输出：
## 无新规则
本次对比未发现可提取的新规则。
'''


class RuleLearner:
    """
    规则学习器
    
    功能：
    - 检测人工修改
    - 分析修改模式
    - 生成并保存新规则
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
            temperature=0.3,  # 低温度，更精确的分析
            max_tokens=4096
        )
        
        # 规则计数器
        self._rule_counter = self._load_rule_counter()
    
    def _load_rule_counter(self) -> int:
        """加载当前规则编号"""
        if not self.prompt_manager:
            return 1
        
        learned_rules = self.prompt_manager.get_learned_rules()
        if not learned_rules:
            return 1
        
        # 从现有规则中提取最大编号
        matches = re.findall(r'## 规则 #(\d+)', learned_rules)
        if matches:
            return max(int(m) for m in matches) + 1
        return 1
    
    def check_for_changes(
        self,
        polished_path: str,
        final_path: str
    ) -> bool:
        """
        检查是否有人工修改
        
        Args:
            polished_path: 润色版文件路径
            final_path: 最终版文件路径
            
        Returns:
            bool: 是否有修改
        """
        polished = Path(polished_path)
        final = Path(final_path)
        
        if not polished.exists() or not final.exists():
            return False
        
        polished_content = polished.read_text(encoding='utf-8')
        final_content = final.read_text(encoding='utf-8')
        
        # 简单比较（去除空白差异）
        return self._normalize(polished_content) != self._normalize(final_content)
    
    def _normalize(self, text: str) -> str:
        """标准化文本用于比较"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def analyze_changes(
        self,
        polished_content: str,
        final_content: str
    ) -> str:
        """
        分析修改并生成规则
        
        Args:
            polished_content: 润色版内容
            final_content: 最终版内容
            
        Returns:
            str: 生成的规则（Markdown格式）
        """
        prompt = DIFF_ANALYSIS_PROMPT.format(
            polished_version=polished_content,
            final_version=final_content,
            rule_number=self._rule_counter,
            date=datetime.now().strftime("%Y-%m-%d")
        )
        
        result = self.llm.generate(prompt, config=self.config)
        return result.content
    
    def learn_from_chapter(
        self,
        chapter_number: int
    ) -> Optional[str]:
        """
        从某章的修改中学习
        
        Args:
            chapter_number: 章节号
            
        Returns:
            str: 学习到的规则，如果没有修改则返回None
        """
        if not self.context_manager or not self.context_manager.project_path:
            raise ValueError("没有加载的项目")
        
        content_dir = self.context_manager.project_path / "content"
        
        polished_path = content_dir / f"ch{chapter_number:03d}_polished.md"
        final_path = content_dir / f"ch{chapter_number:03d}_final.md"
        
        # 检查是否有修改
        if not self.check_for_changes(str(polished_path), str(final_path)):
            return None
        
        # 读取内容
        polished_content = polished_path.read_text(encoding='utf-8')
        final_content = final_path.read_text(encoding='utf-8')
        
        # 分析修改
        new_rules = self.analyze_changes(polished_content, final_content)
        
        # 检查是否有有效规则
        if "无新规则" in new_rules:
            return None
        
        # 保存规则
        if self.prompt_manager:
            self.prompt_manager.append_learned_rule(new_rules)
        
        # 更新计数器
        new_rule_count = len(re.findall(r'## 规则 #\d+', new_rules))
        self._rule_counter += new_rule_count
        
        return new_rules
    
    def learn_from_all_chapters(self) -> Dict[int, str]:
        """
        扫描所有章节，学习修改
        
        Returns:
            Dict[int, str]: 章节号 -> 学习到的规则
        """
        if not self.context_manager or not self.context_manager.project_path:
            raise ValueError("没有加载的项目")
        
        content_dir = self.context_manager.project_path / "content"
        if not content_dir.exists():
            return {}
        
        learned = {}
        
        # 查找所有final文件
        for final_file in content_dir.glob("ch*_final.md"):
            # 提取章节号
            match = re.search(r'ch(\d+)_final\.md', final_file.name)
            if match:
                chapter_num = int(match.group(1))
                
                rules = self.learn_from_chapter(chapter_num)
                if rules:
                    learned[chapter_num] = rules
                    print(f"✅ 从第{chapter_num}章学习到新规则")
        
        return learned
    
    def get_all_learned_rules(self) -> str:
        """获取所有已学习的规则"""
        if self.prompt_manager:
            return self.prompt_manager.get_learned_rules(force_reload=True)
        return ""
    
    def export_rules(self, output_path: str) -> None:
        """
        导出所有规则到指定文件
        
        Args:
            output_path: 输出文件路径
        """
        rules = self.get_all_learned_rules()
        
        header = f'''# 自动学习的润色规则
> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 规则总数: {self._rule_counter - 1}

这些规则是通过分析人工修改自动提取的，将在后续润色中自动应用。

---

'''
        
        Path(output_path).write_text(header + rules, encoding='utf-8')
