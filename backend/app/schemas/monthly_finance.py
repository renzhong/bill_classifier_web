from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

Month = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class AssetItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    kind: Literal["asset", "liability"]


class AssetItemPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    active: bool | None = None


class AssetValueIn(BaseModel):
    amount: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    remark: str | None = Field(default=None, max_length=255)


class InvestmentItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    initial_principal: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    first_month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    linked_asset_item_id: int | None = None


class InvestmentItemPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    initial_principal: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    active: bool | None = None
    linked_asset_item_id: int | None = None


class InvestmentMonthIn(BaseModel):
    buys: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    sells: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    closing_value: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)


class IncomeEntryIn(BaseModel):
    occurred_at: datetime
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    source: str | None = Field(default=None, max_length=64)
    remark: str | None = Field(default=None, max_length=255)


class IncomeEntryPatch(BaseModel):
    occurred_at: datetime | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    source: str | None = Field(default=None, max_length=64)
    remark: str | None = Field(default=None, max_length=255)
