"""
Anthropic Claude API 客户端实现
支持 Claude 3.5 Sonnet, Claude 3 Opus 等模型
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


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude 客户端"""
    
    # 支持的模型
    MODELS = {
        "claude-3-5-sonnet-20241022": {"context": 200000, "input": 3.00, "output": 15.00},
        "claude-3-5-haiku-20241022": {"context": 200000, "input": 0.80, "output": 4.00},
        "claude-3-opus-20240229": {"context": 200000, "input": 15.00, "output": 75.00},
        "claude-3-sonnet-20240229": {"context": 200000, "input": 3.00, "output": 15.00},
        "claude-3-haiku-20240307": {"context": 200000, "input": 0.25, "output": 1.25},
    }
    
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("anthropic package not installed. Run: pip install anthropic")
        else:
            logger.warning("ANTHROPIC_API_KEY not set")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> str:
        """生成文本"""
        if not self.client:
            raise RuntimeError("Claude client not initialized")
        
        config = config or GenerationConfig()
        
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=config.max_tokens,
            system=system_prompt or "You are a helpful AI assistant.",
            messages=[{"role": "user", "content": prompt}],
            temperature=config.temperature,
        )
        
        return response.content[0].text
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """流式生成"""
        if not self.client:
            raise RuntimeError("Claude client not initialized")
        
        config = config or GenerationConfig()
        
        with self.client.messages.stream(
            model=self.model_name,
            max_tokens=config.max_tokens,
            system=system_prompt or "You are a helpful AI assistant.",
            messages=[{"role": "user", "content": prompt}],
            temperature=config.temperature,
        ) as stream:
            for text in stream.text_stream:
                yield text
    
    def chat(
        self,
        messages: List[Message],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> GenerationResult:
        """多轮对话"""
        if not self.client:
            raise RuntimeError("Claude client not initialized")
        
        config = config or GenerationConfig()
        
        # 分离 system 消息
        system = None
        formatted = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                formatted.append({"role": m.role, "content": m.content})
        
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=config.max_tokens,
            system=system or "You are a helpful AI assistant.",
            messages=formatted,
            temperature=config.temperature,
        )
        
        return GenerationResult(
            content=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=self.model_name
        )
    
    def count_tokens(self, text: str) -> int:
        """估算 token 数"""
        # Claude tokenizer 类似 GPT
        return len(text) // 2
    
    @property
    def model_info(self) -> dict:
        """模型信息"""
        return self.MODELS.get(self.model_name, {"context": 200000})
