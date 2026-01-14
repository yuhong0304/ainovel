"""
Core module - 核心架构组件
包含配置、上下文、LLM客户端、Prompt管理和RAG系统
"""

from .config import ConfigLoader, config, get_config
from .context import ContextManager
from .gemini_client import GeminiClient
from .prompt import PromptManager
from .rag import RAGManager

# 别名，保持向后兼容
NovelContext = ContextManager

# 延迟导入多模型客户端以避免可选依赖问题
def __getattr__(name):
    if name == "OpenAIClient":
        from .openai_client import OpenAIClient
        return OpenAIClient
    elif name == "ClaudeClient":
        from .claude_client import ClaudeClient
        return ClaudeClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ConfigLoader",
    "config",
    "get_config",
    "ContextManager",
    "NovelContext",  # 别名
    "GeminiClient",
    "PromptManager",
    "RAGManager",
    "LLMClientFactory",
    "OpenAIClient",
    "ClaudeClient",
]
