"""AI provider 注册器：进程启动时加载全部 provider"""
from __future__ import annotations

from app.ai.base import LLMProvider
from app.ai.providers.claude import ClaudeProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.openai_compat import (
    GLMProvider,
    KimiProvider,
    OpenAIProvider,
    QwenProvider,
)

PROVIDERS: dict[str, LLMProvider] = {}


def _register(p: LLMProvider) -> None:
    PROVIDERS[p.provider_key] = p


for _p in [
    OpenAIProvider(),
    QwenProvider(),
    GLMProvider(),
    KimiProvider(),
    ClaudeProvider(),
    GeminiProvider(),
]:
    _register(_p)


def get_provider(key: str) -> LLMProvider | None:
    return PROVIDERS.get(key)


def list_providers() -> list[dict]:
    return [
        {
            "provider_key": p.provider_key,
            "display_name": p.display_name,
            "default_base_url": p.default_base_url,
            "suggested_models": p.suggested_models,
        }
        for p in PROVIDERS.values()
    ]
