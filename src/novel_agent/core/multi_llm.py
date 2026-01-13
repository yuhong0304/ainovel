"""
多模型LLM客户端
支持 OpenAI GPT-4 和 Anthropic Claude
"""

import os
import logging
from typing import Optional, List, Generator, Any
from abc import ABC, abstractmethod

from .llm_base import (
    BaseLLMClient,
    Message,
    GenerationConfig,
    GenerationResult
)

logger = logging.getLogger(__name__)


# ============ OpenAI 客户端 ============

class OpenAIClient(BaseLLMClient):
    """
    OpenAI GPT 客户端
    
    支持的模型:
    - gpt-4o (推荐)
    - gpt-4-turbo
    - gpt-4
    - gpt-3.5-turbo
    """
    
    # 2026年1月更新
    AVAILABLE_MODELS = [
        # GPT-5 系列 (最新)
        {"name": "gpt-5", "desc": "GPT-5 - 最新旗舰模型", "tier": "flagship"},
        {"name": "gpt-5-mini", "desc": "GPT-5 Mini - 轻量版", "tier": "pro"},
        # GPT-4o 系列
        {"name": "gpt-4o", "desc": "GPT-4o - 多模态旗舰", "tier": "flagship"},
        {"name": "gpt-4o-mini", "desc": "GPT-4o Mini - 快速经济", "tier": "flash"},
        # 经典版
        {"name": "gpt-4-turbo", "desc": "GPT-4 Turbo - 高性能", "tier": "pro"},
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o",
        base_url: Optional[str] = None
    ):
        """
        初始化 OpenAI 客户端
        
        Args:
            api_key: API密钥，默认从环境变量OPENAI_API_KEY读取
            model_name: 模型名称
            base_url: 可选的自定义API地址（用于代理）
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请先安装 openai: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("未提供 OpenAI API Key")
        
        self.model_name = model_name
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        
        logger.info(f"OpenAI 客户端初始化成功，使用模型: {model_name}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """生成内容"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        config = config or GenerationConfig()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
            )
            
            text = response.choices[0].message.content
            usage = response.usage
            
            return GenerationResult(
                text=text,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
                model=self.model_name
            )
            
        except Exception as e:
            logger.error(f"OpenAI 生成失败: {e}")
            raise
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> Generator[str, None, None]:
        """流式生成"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        config = config or GenerationConfig()
        
        try:
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
                    
        except Exception as e:
            logger.error(f"OpenAI 流式生成失败: {e}")
            raise
    
    def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """多轮对话"""
        api_messages = []
        
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            api_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        config = config or GenerationConfig()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=api_messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
            )
            
            text = response.choices[0].message.content
            usage = response.usage
            
            return GenerationResult(
                text=text,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
                model=self.model_name
            )
            
        except Exception as e:
            logger.error(f"OpenAI 对话失败: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """计算token数量"""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model_name)
            return len(encoding.encode(text))
        except:
            # 简单估算
            return len(text) // 4


# ============ Claude 客户端 ============

class ClaudeClient(BaseLLMClient):
    """
    Anthropic Claude 客户端
    
    支持的模型:
    - claude-3-opus (最强)
    - claude-3-sonnet (平衡)
    - claude-3-haiku (快速)
    """
    
    # 2026年1月更新
    AVAILABLE_MODELS = [
        # Claude 4.x 系列 (2025年11月发布)
        {"name": "claude-opus-4.5", "desc": "Claude Opus 4.5 - 最强大，编码与Agent首选", "tier": "flagship"},
        {"name": "claude-sonnet-4.5", "desc": "Claude Sonnet 4.5 - 平衡型，日常推荐", "tier": "pro"},
        {"name": "claude-haiku-4.5", "desc": "Claude Haiku 4.5 - 快速经济", "tier": "flash"},
        # Claude 4.0 系列
        {"name": "claude-opus-4", "desc": "Claude Opus 4 - 强大稳定", "tier": "pro"},
        {"name": "claude-sonnet-4", "desc": "Claude Sonnet 4 - 通用型", "tier": "pro"},
        # Claude 3.5 系列 (Legacy)
        {"name": "claude-3-5-sonnet-20241022", "desc": "Claude 3.5 Sonnet - 经典版", "tier": "legacy"},
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "claude-sonnet-4.5"
    ):
        """
        初始化 Claude 客户端
        
        Args:
            api_key: API密钥，默认从环境变量ANTHROPIC_API_KEY读取
            model_name: 模型名称
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("请先安装 anthropic: pip install anthropic")
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("未提供 Anthropic API Key")
        
        self.model_name = model_name
        self.client = Anthropic(api_key=self.api_key)
        
        logger.info(f"Claude 客户端初始化成功，使用模型: {model_name}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """生成内容"""
        config = config or GenerationConfig()
        
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=config.max_tokens,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
            )
            
            text = response.content[0].text
            
            return GenerationResult(
                text=text,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                model=self.model_name
            )
            
        except Exception as e:
            logger.error(f"Claude 生成失败: {e}")
            raise
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> Generator[str, None, None]:
        """流式生成"""
        config = config or GenerationConfig()
        
        try:
            with self.client.messages.stream(
                model=self.model_name,
                max_tokens=config.max_tokens,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
            ) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Claude 流式生成失败: {e}")
            raise
    
    def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """多轮对话"""
        config = config or GenerationConfig()
        
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=config.max_tokens,
                system=system_prompt or "",
                messages=api_messages,
                temperature=config.temperature,
            )
            
            text = response.content[0].text
            
            return GenerationResult(
                text=text,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                model=self.model_name
            )
            
        except Exception as e:
            logger.error(f"Claude 对话失败: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """估算token数量"""
        # Claude 没有公开的 tokenizer，简单估算
        return len(text) // 4


# ============ 统一客户端工厂 ============

class LLMClientFactory:
    """
    LLM客户端工厂
    
    统一创建不同提供商的客户端
    """
    
    PROVIDERS = {
        "gemini": "GeminiClient",
        "openai": "OpenAIClient",
        "claude": "ClaudeClient"
    }
    
    @classmethod
    def create(
        cls,
        provider: str,
        model_name: Optional[str] = None,
        **kwargs
    ) -> BaseLLMClient:
        """
        创建 LLM 客户端
        
        Args:
            provider: 提供商 (gemini, openai, claude)
            model_name: 模型名称
            **kwargs: 其他参数
            
        Returns:
            LLM客户端实例
        """
        provider = provider.lower()
        
        if provider == "gemini":
            from .gemini_client import GeminiClient
            return GeminiClient(model_name=model_name, **kwargs)
        
        elif provider == "openai":
            return OpenAIClient(model_name=model_name or "gpt-4o", **kwargs)
        
        elif provider == "claude":
            return ClaudeClient(model_name=model_name or "claude-sonnet-4.5", **kwargs)
        
        else:
            raise ValueError(f"不支持的提供商: {provider}")
    
    @classmethod
    def get_available_models(cls, provider: str) -> List[dict]:
        """获取提供商的可用模型列表"""
        provider = provider.lower()
        
        if provider == "gemini":
            from .gemini_client import get_available_models
            return get_available_models()
        
        elif provider == "openai":
            return OpenAIClient.AVAILABLE_MODELS
        
        elif provider == "claude":
            return ClaudeClient.AVAILABLE_MODELS
        
        return []
    
    @classmethod
    def get_all_providers(cls) -> List[Dict[str, Any]]:
        """获取所有支持的提供商"""
        return [
            {
                "id": "gemini",
                "name": "Google Gemini",
                "env_key": "GEMINI_API_KEY",
                "default_model": "gemini-2.5-flash"
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "env_key": "OPENAI_API_KEY",
                "default_model": "gpt-4o"
            },
            {
                "id": "claude",
                "name": "Anthropic Claude",
                "env_key": "ANTHROPIC_API_KEY",
                "default_model": "claude-sonnet-4.5"
            }
        ]
