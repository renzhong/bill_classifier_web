from typing import Any

from pydantic import BaseModel, Field


class StrategyTypeMeta(BaseModel):
    type_key: str
    display_name: str
    description: str
    param_schema: dict


class PipelineStepIn(BaseModel):
    strategy_type: str
    display_name: str = Field(min_length=1, max_length=128)
    params: dict[str, Any] = Field(default_factory=dict)
    sort_order: int = 0
    enabled: bool = True


class PipelineStepPatchIn(BaseModel):
    display_name: str | None = Field(default=None, max_length=128)
    params: dict[str, Any] | None = None
    sort_order: int | None = None
    enabled: bool | None = None


class PipelineStepOut(BaseModel):
    id: int
    strategy_type: str
    display_name: str
    params: dict
    sort_order: int
    enabled: bool

    model_config = {"from_attributes": True}


class ReorderIn(BaseModel):
    order: list[dict]   # [{id, sort_order}]
