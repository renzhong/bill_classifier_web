"""分类引擎内部使用的 in-memory DTO，独立于 parsers.BillItem 与 ORM Bill"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal


@dataclass
class ClassifyBillItem:
    """流经 Pipeline 的账单条目"""

    id: int                      # bills.id（已落库）
    source: str
    payee: str | None
    item_name: str | None
    amount: Decimal
    bill_type: Literal["income", "expense", "other"]
    bill_time: datetime
    owner: str | None = None
    order_id: str | None = None

    # 分类结果（由 StrategyType 写入）
    category_id: int | None = None
    classify_strategy_id: int | None = None
    classify_strategy_type: str | None = None
    lifecycle: str = "unprocessed"
    skip_reason: str | None = None
    ai_provider: str | None = None
    ai_confidence: Decimal | None = None
    manual_overridden: bool = False

    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        """已分类 / 已跳过 / 跨月退款 — 不再被后续 step 处理"""
        return self.lifecycle in ("classified", "skipped", "cross_month_refund")
