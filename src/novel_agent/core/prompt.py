"""
Prompt模板管理器
负责加载、渲染和管理所有Prompt模板
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any
from jinja2 import Environment, FileSystemLoader, Template


class PromptManager:
    """
    Prompt模板管理器
    
    功能:
    - 加载prompts/目录下的所有模板文件
    - 支持Jinja2模板变量渲染
    - 自动注入系统级规则（红线、润色规范）
    - 支持动态加载学习到的新规则
    """
    
    def __init__(self, prompts_dir: str, learned_dir: Optional[str] = None):
        """
        初始化Prompt管理器
        
        Args:
            prompts_dir: prompts目录路径
            learned_dir: 学习规则目录路径（可选）
        """
        self.prompts_dir = Path(prompts_dir)
        self.learned_dir = Path(learned_dir) if learned_dir else self.prompts_dir / "learned"
        
        # 确保目录存在
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.learned_dir.mkdir(parents=True, exist_ok=True)
        
        # Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.prompts_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 缓存加载的模板
        self._cache: Dict[str, str] = {}
        
        # 系统级规则（加载后缓存）
        self._system_rules: Optional[str] = None
        self._writing_style: Optional[str] = None
        self._learned_rules: Optional[str] = None
    
    def load_template(self, template_path: str) -> str:
        """
        加载模板文件内容
        
        Args:
            template_path: 相对于prompts_dir的路径
            
        Returns:
            str: 模板内容
        """
        if template_path in self._cache:
            return self._cache[template_path]
        
        full_path = self.prompts_dir / template_path
        if not full_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {full_path}")
        
        content = full_path.read_text(encoding="utf-8")
        self._cache[template_path] = content
        return content
    
    def render(self, template_path: str, **variables) -> str:
        """
        渲染模板
        
        Args:
            template_path: 模板路径
            **variables: 模板变量
            
        Returns:
            str: 渲染后的文本
        """
        template_content = self.load_template(template_path)
        template = Template(template_content)
        return template.render(**variables)
    
    def get_system_rules(self) -> str:
        """获取核心执行策略与红线"""
        if self._system_rules is None:
            system_path = self.prompts_dir / "system" / "core_rules.md"
            if system_path.exists():
                self._system_rules = system_path.read_text(encoding="utf-8")
            else:
                self._system_rules = ""
        return self._system_rules
    
    def get_writing_style(self) -> str:
        """获取文字润色规范"""
        if self._writing_style is None:
            style_path = self.prompts_dir / "system" / "writing_style.md"
            if style_path.exists():
                self._writing_style = style_path.read_text(encoding="utf-8")
            else:
                self._writing_style = ""
        return self._writing_style
    
    def get_learned_rules(self, force_reload: bool = False) -> str:
        """
        获取学习到的润色规则
        
        Args:
            force_reload: 是否强制重新加载
        """
        if self._learned_rules is None or force_reload:
            rules_path = self.learned_dir / "polish_rules.md"
            if rules_path.exists():
                self._learned_rules = rules_path.read_text(encoding="utf-8")
            else:
                self._learned_rules = ""
        return self._learned_rules
    
    def append_learned_rule(self, rule_content: str) -> None:
        """
        追加新学习到的规则
        
        Args:
            rule_content: 规则内容
        """
        rules_path = self.learned_dir / "polish_rules.md"
        
        # 读取现有内容
        existing = ""
        if rules_path.exists():
            existing = rules_path.read_text(encoding="utf-8")
        
        # 追加新规则
        new_content = existing + "\n\n" + rule_content if existing else rule_content
        rules_path.write_text(new_content, encoding="utf-8")
        
        # 更新缓存
        self._learned_rules = new_content
    
    def build_full_prompt(
        self, 
        stage_template: str,
        include_rules: bool = True,
        include_style: bool = True,
        include_learned: bool = True,
        **variables
    ) -> str:
        """
        构建完整的Prompt（包含系统规则）
        
        Args:
            stage_template: 阶段模板路径
            include_rules: 是否包含核心规则
            include_style: 是否包含文字规范
            include_learned: 是否包含学习规则
            **variables: 模板变量
            
        Returns:
            str: 完整的Prompt
        """
        parts = []
        
        # 系统级规则
        if include_rules:
            rules = self.get_system_rules()
            if rules:
                parts.append("# 核心执行策略与红线\n" + rules)
        
        if include_style:
            style = self.get_writing_style()
            if style:
                parts.append("# 文字润色规范\n" + style)
        
        if include_learned:
            learned = self.get_learned_rules()
            if learned:
                parts.append("# 已学习的润色规则\n" + learned)
        
        # RAG 上下文自动注入
        if "rag_context" in variables and variables["rag_context"]:
            parts.append(f"# 参考资料 (记忆库)\n{variables['rag_context']}")
        
        # 阶段模板
        stage_content = self.render(stage_template, **variables)
        parts.append(stage_content)
        
        return "\n\n---\n\n".join(parts)
    
    def clear_cache(self) -> None:
        """清除所有缓存"""
        self._cache.clear()
        self._system_rules = None
        self._writing_style = None
        self._learned_rules = None
    
    def list_templates(self, subdir: Optional[str] = None) -> list:
        """
        列出所有模板文件
        
        Args:
            subdir: 子目录（可选）
        """
        search_dir = self.prompts_dir / subdir if subdir else self.prompts_dir
        templates = []
        for path in search_dir.rglob("*.md"):
            rel_path = path.relative_to(self.prompts_dir)
            templates.append(str(rel_path))
        return templates
