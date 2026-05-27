from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal


class ParseError(Exception):
    pass


BillTypeLit = Literal["income", "expense", "other"]


@dataclass
class BillItem:
    source: Literal["alipay", "wechat"]
    order_id: str | None
    payee: str | None
    item_name: str | None
    amount: Decimal
    bill_type: BillTypeLit
    bill_time: datetime
    owner: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:
    items: list[BillItem]
    skipped_rows: int = 0
    errors: list[str] = field(default_factory=list)


class Parser(ABC):
    source: str

    @abstractmethod
    def parse(self, data: bytes, owner: str | None = None) -> ParseResult: ...
