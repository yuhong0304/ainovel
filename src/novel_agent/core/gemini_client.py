"""
Gemini API 客户端实现
继承自BaseLLMClient，实现Gemini特定的API调用
"""

import os
import time
import logging
from typing import Generator, Optional, List, Callable, Any

import google.generativeai as genai
from google.generativeai.types import GenerationConfig as GeminiConfig
from google.api_core import exceptions as google_exceptions

from .llm_base import (
    BaseLLMClient, 
    Message, 
    GenerationConfig, 
    GenerationResult
)

# Monkey Patch GenerationConfig if needed or ensure Base has it?
# For now, we assume user passes extra kwargs or we extend the internal config


# 设置日志
logger = logging.getLogger(__name__)


# ============ 自定义异常 ============

class GeminiError(Exception):
    """Gemini API 基础异常"""
    pass


class RateLimitError(GeminiError):
    """API 限流错误"""
    def __init__(self, message: str = "API请求过于频繁，请稍后重试", retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class ContentFilterError(GeminiError):
    """内容安全过滤错误"""
    def __init__(self, message: str = "内容被安全过滤器拦截"):
        super().__init__(message)


class NetworkError(GeminiError):
    """网络连接错误"""
    def __init__(self, message: str = "网络连接失败"):
        super().__init__(message)


class QuotaExceededError(GeminiError):
    """配额超限错误"""
    def __init__(self, message: str = "API配额已用尽"):
        super().__init__(message)


class InvalidResponseError(GeminiError):
    """无效响应错误"""
    def __init__(self, message: str = "API返回无效响应"):
        super().__init__(message)


# ============ Token 成本追踪 ============

class TokenCostTracker:
    """Token 成本追踪器"""
    
    # 定价 (USD per million tokens) - 2026年1月
    PRICING = {
        # Gemini 3.0 系列
        "gemini-3.0-pro": {"input": 2.50, "output": 10.00},
        "gemini-3.0-flash": {"input": 0.15, "output": 0.60},
        # Gemini 2.5 系列
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-2.5-flash-lite": {"input": 0.04, "output": 0.15},
        # Gemini 2.0 系列
        "gemini-2.0-flash": {"input": 0.075, "output": 0.30},
        # Legacy
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    }
    
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.session_costs = []
    
    def track(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        追踪token使用并计算成本
        
        Returns:
            float: 本次调用成本 (USD)
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        # 查找定价
        pricing = self.PRICING.get(model, {"input": 0.075, "output": 0.30})
        
        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
        self.session_costs.append({
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        })
        
        return cost
    
    def get_total_cost(self) -> float:
        """获取总成本"""
        return sum(c["cost"] for c in self.session_costs)
    
    def get_summary(self) -> dict:
        """获取使用摘要"""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": round(self.get_total_cost(), 4),
            "call_count": len(self.session_costs)
        }


# ============ 可用模型列表 (2026年1月更新) ============

AVAILABLE_MODELS = [
    # Gemini 3.0 系列 (2025年11-12月发布，当前最新)
    {"name": "gemini-3.0-pro", "desc": "Gemini 3.0 Pro - 最强大，复杂推理与Agent任务", "tier": "flagship"},
    {"name": "gemini-3.0-flash", "desc": "Gemini 3.0 Flash - Pro级推理，极速响应", "tier": "pro"},
    
    # Gemini 2.5 系列 (2025年6月GA，稳定推荐)
    {"name": "gemini-2.5-pro", "desc": "Gemini 2.5 Pro - 稳定强大，1M上下文", "tier": "pro"},
    {"name": "gemini-2.5-flash", "desc": "Gemini 2.5 Flash - 快速高效，日常首选", "tier": "flash"},
    {"name": "gemini-2.5-flash-lite", "desc": "Gemini 2.5 Flash Lite - 超轻量，成本最优", "tier": "lite"},
    
    # Gemini 2.0 系列
    {"name": "gemini-2.0-flash", "desc": "Gemini 2.0 Flash - 经典稳定", "tier": "flash"},
    
    # 经典版本 (Legacy)
    {"name": "gemini-1.5-pro", "desc": "Gemini 1.5 Pro - 经典版", "tier": "legacy"},
    {"name": "gemini-1.5-flash", "desc": "Gemini 1.5 Flash - 经典版", "tier": "legacy"},
]


def get_available_models() -> list:
    """获取可用模型列表"""
    return AVAILABLE_MODELS


def get_model_by_name(name: str) -> dict:
    """根据名称获取模型信息"""
    for model in AVAILABLE_MODELS:
        if model["name"] == name:
            return model
    return {"name": name, "desc": "未知模型", "tier": "unknown"}


# 全局追踪器
_cost_tracker = TokenCostTracker()


class GeminiClient(BaseLLMClient):
    """
    Gemini API 客户端
    
    支持的模型:
    - gemini-2.0-flash-exp (推荐，速度快)
    - gemini-1.5-pro (更强，适合复杂任务)
    - gemini-1.5-flash (平衡选择)
    """
    
    # 默认模型 (2026年1月推荐)
    DEFAULT_MODEL = "gemini-2.5-flash"
    
    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # 秒
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model_name: Optional[str] = None
    ):
        """
        初始化Gemini客户端
        
        Args:
            api_key: API密钥，默认从环境变量GEMINI_API_KEY读取
            model_name: 模型名称，默认使用gemini-2.0-flash-exp
        """
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "需要提供Gemini API Key。"
                "请设置环境变量 GEMINI_API_KEY 或在初始化时传入 api_key 参数"
            )
        
        model_name = model_name or self.DEFAULT_MODEL
        super().__init__(api_key, model_name)
        
        # 配置API
        genai.configure(api_key=api_key)
        self._model = None
    
    def _get_model(self, system_prompt: Optional[str] = None):
        """获取或创建模型实例"""
        # 每次都创建新实例以支持不同的system_prompt
        return genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt
        )
    
    def _to_gemini_config(self, config: Optional[GenerationConfig]) -> GeminiConfig:
        """转换为Gemini配置格式"""
        if config is None:
            config = GenerationConfig()
        
        return GeminiConfig(
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
            top_p=config.top_p,
            top_k=config.top_k,
            response_mime_type=getattr(config, "response_mime_type", "text/plain")
        )
    
    def _retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """
        带重试的调用，针对不同错误类型采用不同策略
        
        Raises:
            RateLimitError: API限流
            ContentFilterError: 内容被过滤
            NetworkError: 网络问题
            QuotaExceededError: 配额超限
            GeminiError: 其他API错误
        """
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
                
            except google_exceptions.ResourceExhausted as e:
                # 配额或限流错误
                error_msg = str(e).lower()
                if "quota" in error_msg:
                    logger.error(f"API配额已用尽: {e}")
                    raise QuotaExceededError(f"API配额已用尽: {e}")
                else:
                    # 限流 - 等待更长时间
                    wait_time = self.RETRY_DELAY * (attempt + 2) * 2
                    logger.warning(f"API限流，等待 {wait_time}s 后重试 (尝试 {attempt + 1}/{self.MAX_RETRIES})")
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(wait_time)
                    last_error = RateLimitError(str(e))
                    
            except google_exceptions.InvalidArgument as e:
                # 内容过滤或无效请求
                error_msg = str(e).lower()
                if "safety" in error_msg or "blocked" in error_msg:
                    logger.error(f"内容被安全过滤器拦截: {e}")
                    raise ContentFilterError(f"内容被安全过滤器拦截: {e}")
                else:
                    logger.error(f"无效请求参数: {e}")
                    raise GeminiError(f"无效请求参数: {e}")
                    
            except (google_exceptions.ServiceUnavailable, 
                    google_exceptions.DeadlineExceeded) as e:
                # 服务不可用或超时 - 重试
                wait_time = self.RETRY_DELAY * (attempt + 1)
                logger.warning(f"服务暂时不可用，等待 {wait_time}s 后重试 (尝试 {attempt + 1}/{self.MAX_RETRIES})")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(wait_time)
                last_error = NetworkError(str(e))
                
            except ConnectionError as e:
                # 网络连接错误
                wait_time = self.RETRY_DELAY * (attempt + 1)
                logger.warning(f"网络连接失败，等待 {wait_time}s 后重试 (尝试 {attempt + 1}/{self.MAX_RETRIES})")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(wait_time)
                last_error = NetworkError(str(e))
                
            except Exception as e:
                # 其他错误
                error_msg = str(e).lower()
                
                # 检查是否是可重试的通用错误
                if any(keyword in error_msg for keyword in ["timeout", "connection", "network"]):
                    wait_time = self.RETRY_DELAY * (attempt + 1)
                    logger.warning(f"临时错误，等待 {wait_time}s 后重试: {e}")
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(wait_time)
                    last_error = NetworkError(str(e))
                else:
                    # 不可重试的错误，直接抛出
                    logger.error(f"不可重试的错误: {e}")
                    raise GeminiError(f"API调用失败: {e}")
        
        # 所有重试都失败了
        if last_error:
            raise last_error
        raise GeminiError("未知错误")
    
    def generate(
        self, 
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """同步生成文本"""
        model = self._get_model(system_prompt)
        gemini_config = self._to_gemini_config(config)
        
        response = self._retry_with_backoff(
            model.generate_content,
            prompt,
            generation_config=gemini_config
        )
        
        # 提取token统计
        usage = getattr(response, 'usage_metadata', None)
        input_tokens = getattr(usage, 'prompt_token_count', 0) if usage else 0
        output_tokens = getattr(usage, 'candidates_token_count', 0) if usage else 0
        
        # 追踪成本
        cost = _cost_tracker.track(self.model_name, input_tokens, output_tokens)
        logger.debug(f"Token使用: 输入={input_tokens}, 输出={output_tokens}, 成本=${cost:.6f}")
        
        return GenerationResult(
            content=response.text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model_name
        )
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> Generator[str, None, None]:
        """流式生成文本"""
        model = self._get_model(system_prompt)
        gemini_config = self._to_gemini_config(config)
        
        response = model.generate_content(
            prompt,
            generation_config=gemini_config,
            stream=True
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
    
    def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """多轮对话"""
        model = self._get_model(system_prompt)
        gemini_config = self._to_gemini_config(config)
        
        # 转换消息格式为Gemini格式
        history = []
        for msg in messages[:-1]:  # 除了最后一条
            role = "user" if msg.role == "user" else "model"
            history.append({"role": role, "parts": [msg.content]})
        
        # 创建聊天会话
        chat = model.start_chat(history=history)
        
        # 发送最后一条消息
        last_message = messages[-1].content if messages else ""
        response = self._retry_with_backoff(
            chat.send_message,
            last_message,
            generation_config=gemini_config
        )
        
        usage = getattr(response, 'usage_metadata', None)
        input_tokens = getattr(usage, 'prompt_token_count', 0) if usage else 0
        output_tokens = getattr(usage, 'candidates_token_count', 0) if usage else 0
        
        return GenerationResult(
            content=response.text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model_name
        )
    
    def count_tokens(self, text: str) -> int:
        """计算Token数量"""
        model = self._get_model()
        result = model.count_tokens(text)
        return result.total_tokens


# 便捷函数：创建默认客户端
def create_gemini_client(
    api_key: Optional[str] = None,
    model: str = "gemini-2.0-flash-exp"
) -> GeminiClient:
    """
    创建Gemini客户端的便捷函数
    
    Args:
        api_key: API密钥，默认从环境变量读取
        model: 模型名称
        
    Returns:
        GeminiClient: 客户端实例
    """
    return GeminiClient(api_key=api_key, model_name=model)


def get_cost_tracker() -> TokenCostTracker:
    """获取全局成本追踪器"""
    return _cost_tracker


def get_usage_summary() -> dict:
    """获取Token使用摘要"""
    return _cost_tracker.get_summary()


def reset_cost_tracker() -> None:
    """重置成本追踪器"""
    global _cost_tracker
    _cost_tracker = TokenCostTracker()

