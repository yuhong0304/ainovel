"""
Core module - 核心架构组件
包含配置、上下文、LLM客户端、Prompt管理和RAG系统
"""

from .config import ConfigLoader, config, get_config
from .context import NovelContext
from .gemini_client import GeminiClient
from .prompt import PromptManager
from .rag import RAGManager

# 延迟导入多模型客户端以避免可选依赖问题
def __getattr__(name):
    if name == "LLMClientFactory":
        from .multi_llm import LLMClientFactory
        return LLMClientFactory
    elif name == "OpenAIClient":
        from .multi_llm import OpenAIClient
        return OpenAIClient
    elif name == "ClaudeClient":
        from .multi_llm import ClaudeClient
        return ClaudeClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ConfigLoader",
    "config",
    "get_config",
    "NovelContext", 
    "GeminiClient",
    "PromptManager",
    "RAGManager",
    "LLMClientFactory",
    "OpenAIClient",
    "ClaudeClient",
]
