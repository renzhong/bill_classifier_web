from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UploadTaskOut(BaseModel):
    id: int
    source: str
    filename: str
    file_size: int
    status: str
    total_rows: int
    classified_rows: int
    error_msg: str | None
    parse_errors: list[str] = []
    tag_ids: list[int] = []
    owner_label: str | None
    created_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class BillOut(BaseModel):
    id: int
    source: str
    owner: str | None
    order_id: str | None
    payee: str | None
    item_name: str | None
    amount: Decimal
    bill_type: str
    bill_time: datetime
    bill_month: str | None
    category_id: int | None
    classify_strategy_id: int | None
    classify_strategy_type: str | None
    lifecycle: str
    skip_reason: str | None
    ai_provider: str | None
    ai_confidence: Decimal | None
    manual_overridden: bool
    archived: bool
    tag_ids: list[int] = []

    model_config = {"from_attributes": True}


class BillListOut(BaseModel):
    items: list[BillOut]
    total: int
    page: int
    page_size: int


class BillPatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: int | None = None
    tag_ids: list[int] | None = None  # retained only to return a clear legacy API error


class BatchActionIn(BaseModel):
    ids: list[int] = Field(min_length=1)
    action: Literal["set_category", "add_tag", "remove_tag", "delete"]
    payload: dict = Field(default_factory=dict)
