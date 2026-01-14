"""
OpenAI API 客户端实现
支持 GPT-4, GPT-4o, o1 系列模型
"""

import os
import logging
from typing import Generator, Optional, List

from .llm_base import (
    BaseLLMClient, 
    Message, 
    GenerationConfig, 
    GenerationResult
)

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT 客户端"""
    
    # 支持的模型
    MODELS = {
        "gpt-4o": {"context": 128000, "input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"context": 128000, "input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"context": 128000, "input": 10.00, "output": 30.00},
        "o1": {"context": 200000, "input": 15.00, "output": 60.00},
        "o1-mini": {"context": 128000, "input": 3.00, "output": 12.00},
    }
    
    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("openai package not installed. Run: pip install openai")
        else:
            logger.warning("OPENAI_API_KEY not set")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> str:
        """生成文本"""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        config = config or GenerationConfig()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
        )
        
        return response.choices[0].message.content
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """流式生成"""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        config = config or GenerationConfig()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def chat(
        self,
        messages: List[Message],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> GenerationResult:
        """多轮对话"""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        config = config or GenerationConfig()
        
        formatted = [{"role": m.role, "content": m.content} for m in messages]
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=formatted,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
        )
        
        return GenerationResult(
            content=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            model=self.model_name
        )
    
    def count_tokens(self, text: str) -> int:
        """估算 token 数"""
        # 粗略估计: 英文 4 字符/token, 中文 2 字符/token
        return len(text) // 2
    
    @property
    def model_info(self) -> dict:
        """模型信息"""
        return self.MODELS.get(self.model_name, {"context": 128000})
