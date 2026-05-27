"""LLMProvider 抽象与统一输出"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ClassifyResult:
    category: str | None         # 命中的 category.name；None 表示模型放弃
    confidence: Decimal | None   # 0-1 之间；可空
    raw: str                     # 模型的原始返回（debug）


class LLMProvider(ABC):
    provider_key: str            # openai / qwen / glm / kimi / claude / gemini
    display_name: str
    default_base_url: str | None = None
    suggested_models: list[str] = []

    @abstractmethod
    async def chat(self, *, prompt: str, model: str, api_key: str, base_url: str | None) -> str:
        """发起一次同步语义的 chat 调用，返回纯文本结果。
        实现者负责处理 SDK 差异；上层会做 JSON 解析与重试策略。
        """


class ProviderError(Exception):
    pass
