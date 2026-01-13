"""
Pipeline 模块测试
"""

import pytest
from unittest.mock import MagicMock, patch


class TestPipelineImports:
    """测试 Pipeline 模块导入"""

    def test_import_pipeline_module(self):
        """测试导入 pipeline 模块"""
        from novel_agent import pipeline
        assert pipeline is not None

    def test_import_stages(self):
        """测试导入各个阶段"""
        from novel_agent.pipeline import (
            MetaPromptGenerator,
            MasterOutlineGenerator,
            VolumeOutlineGenerator,
            ChapterOutlineGenerator,
            ContentGenerator,
        )
        
        assert MetaPromptGenerator is not None
        assert MasterOutlineGenerator is not None
        assert VolumeOutlineGenerator is not None
        assert ChapterOutlineGenerator is not None
        assert ContentGenerator is not None


class TestMetaPromptGenerator:
    """元提示生成器测试"""

    def test_meta_generator_init(self):
        """测试元提示生成器初始化"""
        from novel_agent.pipeline import MetaPromptGenerator
        
        # 使用 mock LLM
        mock_llm = MagicMock()
        generator = MetaPromptGenerator(mock_llm)
        assert generator is not None
