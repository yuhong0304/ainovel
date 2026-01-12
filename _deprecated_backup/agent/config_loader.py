"""
配置加载器
统一管理项目配置
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ConfigLoader:
    """
    配置加载器
    
    功能：
    - 加载 config.yaml
    - 提供配置项访问
    - 支持环境变量覆盖
    """
    
    _instance: Optional['ConfigLoader'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._config:
            self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        # 查找配置文件
        config_paths = [
            Path(__file__).parent.parent / "config.yaml",
            Path.cwd() / "config.yaml",
        ]
        
        for path in config_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                break
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
    
    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖"""
        # LLM 模型
        if os.getenv("GEMINI_MODEL"):
            self._config.setdefault("llm", {})["model"] = os.getenv("GEMINI_MODEL")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项（支持点号分隔的路径）
        
        Args:
            key: 配置键，如 "llm.model" 或 "novel.words_per_chapter"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self._config.get("llm", {})
    
    def get_novel_config(self) -> Dict[str, Any]:
        """获取小说参数配置"""
        return self._config.get("novel", {})
    
    def get_paths_config(self) -> Dict[str, Any]:
        """获取路径配置"""
        return self._config.get("paths", {})
    
    def get_cost_config(self) -> Dict[str, Any]:
        """获取成本追踪配置"""
        return self._config.get("cost_tracking", {})
    
    def reload(self) -> None:
        """重新加载配置"""
        self._config = {}
        self._load_config()


# 全局配置实例
config = ConfigLoader()


def get_config(key: str, default: Any = None) -> Any:
    """便捷函数：获取配置项"""
    return config.get(key, default)
