"""Anthropic Claude provider"""
from __future__ import annotations

from app.ai.base import LLMProvider, ProviderError


class ClaudeProvider(LLMProvider):
    provider_key = "claude"
    display_name = "Anthropic Claude"
    default_base_url = None        # SDK 内部默认
    suggested_models = ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"]
    timeout: float = 30.0
    max_tokens: int = 512

    async def chat(self, *, prompt: str, model: str, api_key: str, base_url: str | None) -> str:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as e:  # pragma: no cover
            raise ProviderError("anthropic SDK not installed") from e

        kwargs: dict = {"api_key": api_key, "timeout": self.timeout}
        if base_url:
            kwargs["base_url"] = base_url
        client = AsyncAnthropic(**kwargs)
        try:
            resp = await client.messages.create(
                model=model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            raise ProviderError(f"claude call failed: {e}") from e

        # Anthropic 返回 content 是一个 block 列表，取 text 拼接
        parts: list[str] = []
        for block in resp.content or []:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "".join(parts).strip()
