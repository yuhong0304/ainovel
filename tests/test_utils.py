"""
Utils 模块测试
"""

import pytest


class TestCommonUtils:
    """通用工具函数测试"""

    def test_count_words_chinese(self):
        """测试中文字数统计"""
        from novel_agent.utils.common import count_words
        
        text = "这是一段测试文本"
        count = count_words(text)
        assert count == 8  # 8个中文字符

    def test_count_words_mixed(self):
        """测试中英混合字数统计"""
        from novel_agent.utils.common import count_words
        
        text = "Hello 世界"
        count = count_words(text)
        # 应该统计中文字符 + 英文单词
        assert count > 0

    def test_count_words_empty(self):
        """测试空字符串"""
        from novel_agent.utils.common import count_words
        
        count = count_words("")
        assert count == 0
