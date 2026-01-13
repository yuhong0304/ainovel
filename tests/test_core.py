"""
Core 模块测试
"""

import pytest
from unittest.mock import patch, MagicMock


class TestConfigLoader:
    """配置加载器测试"""

    def test_config_singleton(self):
        """测试配置为单例模式"""
        from novel_agent.core.config import ConfigLoader
        
        config1 = ConfigLoader()
        config2 = ConfigLoader()
        assert config1 is config2

    def test_config_get_with_default(self):
        """测试获取配置默认值"""
        from novel_agent.core.config import config
        
        result = config.get("nonexistent.key", "default_value")
        assert result == "default_value"

    def test_config_get_nested(self):
        """测试获取嵌套配置"""
        from novel_agent.core.config import config
        
        # 由于配置文件可能不存在，我们测试返回值类型
        result = config.get("llm.model")
        # 结果应该是字符串或None
        assert result is None or isinstance(result, str)


class TestPromptManager:
    """Prompt管理器测试"""

    def test_prompt_manager_init(self):
        """测试 PromptManager 初始化"""
        from novel_agent.core.prompt import PromptManager
        
        # 不传参数应该不会报错
        pm = PromptManager()
        assert pm is not None


class TestNovelContext:
    """小说上下文测试"""

    def test_context_init(self):
        """测试上下文初始化"""
        from novel_agent.core.context import NovelContext
        
        # 默认初始化
        ctx = NovelContext()
        assert ctx is not None
