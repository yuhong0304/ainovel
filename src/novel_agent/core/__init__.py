"""
Core module - 核心架构组件
包含配置、上下文、LLM客户端、Prompt管理和RAG系统
"""

from .config import ConfigLoader, config, get_config
from .context import NovelContext
from .gemini_client import GeminiClient
from .prompt import PromptManager
from .rag import RAGManager
from .multi_llm import LLMClientFactory, OpenAIClient, ClaudeClient

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


