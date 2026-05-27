from pydantic import BaseModel, Field


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    display_name: str | None = Field(default=None, max_length=64)
    color: str | None = Field(default=None, max_length=16)
    sort_order: int = 0


class CategoryPatchIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    display_name: str | None = Field(default=None, max_length=64)
    color: str | None = Field(default=None, max_length=16)
    sort_order: int | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    display_name: str | None
    color: str | None
    sort_order: int

    model_config = {"from_attributes": True}


class CategoryReorderIn(BaseModel):
    order: list[dict]    # [{id: int, sort_order: int}]


class TagIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    color: str | None = Field(default=None, max_length=16)


class TagOut(BaseModel):
    id: int
    name: str
    color: str | None

    model_config = {"from_attributes": True}


class DictIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    target_field: str = Field(default="any", pattern="^(payee|item_name|any)$")
    remark: str | None = Field(default=None, max_length=255)


class DictPatchIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    target_field: str | None = Field(default=None, pattern="^(payee|item_name|any)$")
    remark: str | None = Field(default=None, max_length=255)


class DictOut(BaseModel):
    id: int
    name: str
    target_field: str
    remark: str | None
    entry_count: int = 0

    model_config = {"from_attributes": True}


class DictEntryIn(BaseModel):
    key_text: str = Field(min_length=1, max_length=255)
    category_id: int


class DictEntryOut(BaseModel):
    id: int
    key_text: str
    category_id: int

    model_config = {"from_attributes": True}


class DictBulkImportIn(BaseModel):
    csv_text: str        # 每行 "key,category_name"，忽略空行与 # 注释
