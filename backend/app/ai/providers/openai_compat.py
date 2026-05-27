"""OpenAI / Qwen / GLM / Kimi 等共用 OpenAI 兼容协议的 provider 实现。

四个 provider 共享一份代码，仅 ``provider_key`` / ``default_base_url`` / ``suggested_models`` 不同。
"""
from __future__ import annotations

from app.ai.base import LLMProvider, ProviderError


class _OpenAICompatBase(LLMProvider):
    timeout: float = 30.0

    async def chat(self, *, prompt: str, model: str, api_key: str, base_url: str | None) -> str:
        # 懒加载 openai SDK，避免无 AI 场景的导入开销
        try:
            from openai import AsyncOpenAI
        except ImportError as e:  # pragma: no cover
            raise ProviderError("openai SDK not installed") from e

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or self.default_base_url,
            timeout=self.timeout,
        )
        try:
            resp = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
        except Exception as e:
            raise ProviderError(f"{self.provider_key} call failed: {e}") from e
        finally:
            await client.close()
        return (resp.choices[0].message.content or "").strip()


class OpenAIProvider(_OpenAICompatBase):
    provider_key = "openai"
    display_name = "OpenAI"
    default_base_url = "https://api.openai.com/v1"
    suggested_models = ["gpt-4o", "gpt-4o-mini", "gpt-4.1-mini"]


class QwenProvider(_OpenAICompatBase):
    provider_key = "qwen"
    display_name = "通义千问 (Qwen)"
    default_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    suggested_models = ["qwen-plus", "qwen-max", "qwen-turbo"]


class GLMProvider(_OpenAICompatBase):
    provider_key = "glm"
    display_name = "智谱 GLM"
    default_base_url = "https://open.bigmodel.cn/api/paas/v4"
    suggested_models = ["glm-4-plus", "glm-4-air", "glm-4-flash"]


class KimiProvider(_OpenAICompatBase):
    provider_key = "kimi"
    display_name = "月之暗面 Kimi"
    default_base_url = "https://api.moonshot.cn/v1"
    suggested_models = ["moonshot-v1-32k", "moonshot-v1-8k"]
