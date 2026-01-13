"""
Core module - 核心架构组件
包含配置、上下文、LLM客户端、Prompt管理和RAG系统
"""

from .config import Config
from .context import NovelContext
from .gemini_client import GeminiClient
from .prompt import PromptManager
from .rag import RAGManager

__all__ = [
    "Config",
    "NovelContext", 
    "GeminiClient",
    "PromptManager",
    "RAGManager",
]
