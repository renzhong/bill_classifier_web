"""把"用户多条文本规则 + 当前账单"组装成发给 LLM 的最终 prompt。

设计原则：
- 提示词放在代码里集中维护，避免散落
- 提供 build_prompt() 给 strategy 用，也提供 preview_prompt() 给前端预览
- 模型只需返回类别名，便于解析
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.classify.bill_item import ClassifyBillItem


SYSTEM_TEMPLATE = """你是一个账单分类助手。需要根据用户提供的"分类规则"把一条账单归到给定的类别清单中的一个。

【可选类别】
{categories}

【用户规则】（按顺序参考，规则之间没有强弱关系，仅供参考）
{rules}

【输出要求】
- 只输出一个类别名，必须是上面"可选类别"中的一项
- 如果没有任何类别合适，输出: UNKNOWN
- 不要解释，不要标点，不要前后缀

【待分类账单】
- 收款方: {payee}
- 商品/描述: {item_name}
- 金额: {amount}
- 类型: {bill_type}
- 时间: {bill_time}
- 来源: {source}
"""


def _format_categories(category_names: list[str]) -> str:
    if not category_names:
        return "（用户未创建类别）"
    return "\n".join(f"- {n}" for n in category_names)


def _format_rules(rules: list[str]) -> str:
    cleaned = [r.strip() for r in rules if r and r.strip()]
    if not cleaned:
        return "（无）"
    return "\n".join(f"{i + 1}. {r}" for i, r in enumerate(cleaned))


def build_prompt(
    *,
    rules: list[str],
    category_names: list[str],
    bill: "ClassifyBillItem",
) -> str:
    return SYSTEM_TEMPLATE.format(
        categories=_format_categories(category_names),
        rules=_format_rules(rules),
        payee=bill.payee or "",
        item_name=bill.item_name or "",
        amount=str(bill.amount),
        bill_type=bill.bill_type,
        bill_time=bill.bill_time.strftime("%Y-%m-%d %H:%M:%S"),
        source=bill.source,
    )


def preview_prompt(*, rules: list[str], category_names: list[str]) -> str:
    """给前端预览：用占位账单填充"""
    return SYSTEM_TEMPLATE.format(
        categories=_format_categories(category_names),
        rules=_format_rules(rules),
        payee="<示例收款方>",
        item_name="<示例商品名>",
        amount="0.00",
        bill_type="expense",
        bill_time="2026-01-01 12:00:00",
        source="alipay",
    )


def parse_response(text: str, valid_categories: list[str]) -> str | None:
    """从模型返回里提取分类名；找不到合法类别返回 None"""
    cleaned = (text or "").strip().splitlines()
    candidate = cleaned[0].strip() if cleaned else ""
    # 去掉常见包裹符号
    candidate = candidate.strip("`*\"' 、，。.,:：")
    if not candidate or candidate.upper() == "UNKNOWN":
        return None
    for name in valid_categories:
        if name == candidate or name in candidate:
            return name
    return None
