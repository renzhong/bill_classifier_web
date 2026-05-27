from datetime import datetime

from pydantic import BaseModel, Field


class AiCredentialIn(BaseModel):
    provider: str = Field(min_length=1, max_length=32)
    model_name: str = Field(min_length=1, max_length=64)
    api_key: str = Field(min_length=1)
    base_url: str | None = Field(default=None, max_length=255)
    enabled: bool = True


class AiCredentialPatchIn(BaseModel):
    model_name: str | None = Field(default=None, max_length=64)
    api_key: str | None = None
    base_url: str | None = Field(default=None, max_length=255)
    enabled: bool | None = None


class AiCredentialOut(BaseModel):
    id: int
    provider: str
    model_name: str
    base_url: str | None
    enabled: bool
    has_api_key: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class AiStrategyIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    strategy_text: str = ""
    active: bool = False
    credential_id: int | None = None


class AiStrategyPatchIn(BaseModel):
    name: str | None = Field(default=None, max_length=64)
    strategy_text: str | None = None
    active: bool | None = None
    credential_id: int | None = None


class AiStrategyOut(BaseModel):
    id: int
    name: str
    strategy_text: str
    active: bool
    credential_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PreviewIn(BaseModel):
    strategy_text: str = ""


class PreviewOut(BaseModel):
    prompt: str


class TestIn(BaseModel):
    credential_id: int
    strategy_id: int | None = None
    sample: dict


class TestOut(BaseModel):
    category: str | None
    confidence: str | None
    raw: str


class ProviderMetaOut(BaseModel):
    provider_key: str
    display_name: str
    default_base_url: str | None
    suggested_models: list[str]
