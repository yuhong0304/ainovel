"""
Novel Agent 测试套件
"""

import pytest
from pathlib import Path


# 测试根目录
TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent


@pytest.fixture
def project_root():
    """返回项目根目录"""
    return PROJECT_ROOT


@pytest.fixture
def sample_config():
    """返回示例配置"""
    return {
        "llm": {
            "model": "gemini-2.0-flash-exp",
            "max_retries": 3,
            "retry_delay": 2,
        },
        "novel": {
            "words_per_chapter": 3000,
            "word_tolerance": 200,
        }
    }
