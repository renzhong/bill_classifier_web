"""Google Gemini provider（google-generativeai 同步 SDK，包装到线程池里跑）"""
from __future__ import annotations

import asyncio

from app.ai.base import LLMProvider, ProviderError


class GeminiProvider(LLMProvider):
    provider_key = "gemini"
    display_name = "Google Gemini"
    default_base_url = None
    suggested_models = ["gemini-1.5-pro", "gemini-1.5-flash"]

    async def chat(self, *, prompt: str, model: str, api_key: str, base_url: str | None) -> str:
        try:
            import google.generativeai as genai
        except ImportError as e:  # pragma: no cover
            raise ProviderError("google-generativeai not installed") from e

        def _call() -> str:
            genai.configure(api_key=api_key)
            m = genai.GenerativeModel(model)
            resp = m.generate_content(prompt)
            return (getattr(resp, "text", "") or "").strip()

        try:
            return await asyncio.to_thread(_call)
        except Exception as e:
            raise ProviderError(f"gemini call failed: {e}") from e
