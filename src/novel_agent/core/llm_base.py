"""
LLM客户端抽象基类
定义所有LLM API客户端必须实现的接口，便于后续扩展支持其他模型
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator, Optional, Dict, Any, List


@dataclass
class Message:
    """聊天消息"""
    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class GenerationConfig:
    """生成配置"""
    temperature: float = 0.7
    max_tokens: int = 8192
    top_p: float = 0.95
    top_k: int = 40


@dataclass  
class GenerationResult:
    """生成结果"""
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class BaseLLMClient(ABC):
    """
    LLM客户端抽象基类
    
    所有具体的LLM实现（Gemini, Claude, GPT等）都需要继承此类
    并实现以下抽象方法
    """
    
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
    
    @abstractmethod
    def generate(
        self, 
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """
        同步生成文本
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            config: 生成配置
            
        Returns:
            GenerationResult: 生成结果
        """
        pass
    
    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> Generator[str, None, None]:
        """
        流式生成文本
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            config: 生成配置
            
        Yields:
            str: 生成的文本片段
        """
        pass
    
    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """
        多轮对话
        
        Args:
            messages: 历史消息列表
            system_prompt: 系统提示词
            config: 生成配置
            
        Returns:
            GenerationResult: 生成结果
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        计算文本的Token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: Token数量
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "client_type": self.__class__.__name__
        }
