"""
全局应用状态
"""
import os
import sys
from pathlib import Path
from typing import Optional

# 添加agent目录到路径
# web module -> novel_agent package -> src
current_dir = Path(__file__).parent
agent_dir = current_dir.parent
src_dir = agent_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from novel_agent.core.gemini_client import (
    GeminiClient, 
    get_usage_summary, 
    get_available_models,
    get_model_by_name,
    reset_cost_tracker
)
from novel_agent.core.prompt import PromptManager
from novel_agent.core.context import ContextManager
from novel_agent.core.rag import RAGManager

# 基础路径配置
BASE_DIR = agent_dir
PROMPTS_DIR = BASE_DIR / "prompts"
PROJECTS_DIR = Path.cwd() / "projects"
RAG_DIR = Path.cwd() / "data" / "rag_store"

# 确保目录存在
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
RAG_DIR.mkdir(parents=True, exist_ok=True)


class AppState:
    """应用全局状态"""
    def __init__(self):
        self.llm = None  # 当前 LLM 客户端
        self.prompt_manager: Optional[PromptManager] = None
        self.context_manager: Optional[ContextManager] = None
        self.rag_manager: Optional[RAGManager] = None
        self.current_model: str = "gemini-2.0-flash-exp" # Default to a safe model or env
        self.current_provider: str = "gemini"  # gemini | openai | claude
        
        # 生成进度队列
        self.progress_queues: dict = {}
        
        # 批量任务
        self.batch_jobs: dict = {}
        
        # 生成参数配置
        self.generation_config = {
            "temperature": 0.7,
            "max_tokens": 8192,
            "top_p": 0.95,
            "top_k": 40,
            "theme": "dark"
        }
        
        # 安全设置
        self.safety_settings = {
            "harm_block_threshold": "BLOCK_MEDIUM_AND_ABOVE",
            "enable_content_filter": True,
            "harassment": "block_none",
            "hate_speech": "block_none",
            "sexually_explicit": "block_none",
            "dangerous_content": "block_none"
        }
        
        # 参数预设
        self.config_presets = {
            "creative": {"temperature": 1.0, "max_tokens": 8192, "top_p": 0.95, "top_k": 50},
            "balanced": {"temperature": 0.7, "max_tokens": 8192, "top_p": 0.9, "top_k": 40},
            "precise": {"temperature": 0.3, "max_tokens": 4096, "top_p": 0.8, "top_k": 20}
        }
        
    def initialize(self):
        """初始化"""
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.current_model = model_name
        self.current_provider = "gemini"
        
        # 尝试初始化 LLM，如果失败（如没有 Key）则保持为 None
        try:
            if os.getenv("GEMINI_API_KEY"):
                self.llm = GeminiClient(model_name=model_name)
        except Exception as e:
            print(f"Warning: Failed to init GeminiClient: {e}")
            
        self.prompt_manager = PromptManager(str(PROMPTS_DIR))
        self.context_manager = ContextManager(str(PROJECTS_DIR))
        
        try:
            self.rag_manager = RAGManager(str(RAG_DIR))
            print(f"✓ RAG 系统已就绪: {RAG_DIR}")
        except Exception as e:
             print(f"Warning: Failed to init RAGManager: {e}")
        
    def switch_model(self, model_name: str, provider: str = None):
        """切换模型"""
        # 自动检测 provider
        if provider is None:
            if model_name.startswith("gemini"):
                provider = "gemini"
            elif model_name.startswith("gpt") or model_name.startswith("o1"):
                provider = "openai"
            elif model_name.startswith("claude"):
                provider = "claude"
            else:
                provider = "gemini"
        
        self.current_provider = provider
        self.current_model = model_name
        
        if provider == "gemini":
            self.llm = GeminiClient(model_name=model_name)
        elif provider == "openai":
            from novel_agent.core.openai_client import OpenAIClient
            self.llm = OpenAIClient(model_name=model_name)
        elif provider == "claude":
            from novel_agent.core.claude_client import ClaudeClient
            self.llm = ClaudeClient(model_name=model_name)
    
    def get_llm_config(self):
        """获取LLM配置对象"""
        from novel_agent.core.llm_base import GenerationConfig
        return GenerationConfig(
            temperature=self.generation_config["temperature"],
            max_tokens=self.generation_config["max_tokens"],
            top_p=self.generation_config["top_p"],
            top_k=self.generation_config["top_k"]
        )


# Global Instance
state = AppState()
