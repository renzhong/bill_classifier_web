from decimal import Decimal

from pydantic import BaseModel, Field


class AssetIn(BaseModel):
    snapshot_month: str = Field(min_length=7, max_length=7)        # YYYY-MM
    asset_type: str = Field(pattern="^(cash|deposit|stock|fund|other)$")
    account_name: str = Field(min_length=1, max_length=64)
    amount: Decimal
    remark: str | None = Field(default=None, max_length=255)


class AssetPatchIn(BaseModel):
    snapshot_month: str | None = Field(default=None, min_length=7, max_length=7)
    asset_type: str | None = Field(default=None, pattern="^(cash|deposit|stock|fund|other)$")
    account_name: str | None = Field(default=None, max_length=64)
    amount: Decimal | None = None
    remark: str | None = Field(default=None, max_length=255)


class AssetOut(BaseModel):
    id: int
    snapshot_month: str
    asset_type: str
    account_name: str
    amount: Decimal
    remark: str | None

    model_config = {"from_attributes": True}


class CopyAssetsIn(BaseModel):
    from_month: str = Field(min_length=7, max_length=7)
    to_month: str = Field(min_length=7, max_length=7)
    overwrite: bool = False


class IncomeIn(BaseModel):
    year_month: str = Field(min_length=7, max_length=7)
    source: str = Field(min_length=1, max_length=64)
    amount: Decimal
    remark: str | None = Field(default=None, max_length=255)


class IncomePatchIn(BaseModel):
    year_month: str | None = Field(default=None, min_length=7, max_length=7)
    source: str | None = Field(default=None, max_length=64)
    amount: Decimal | None = None
    remark: str | None = Field(default=None, max_length=255)


class IncomeOut(BaseModel):
    id: int
    year_month: str
    source: str
    amount: Decimal
    remark: str | None

    model_config = {"from_attributes": True}
