"""StrategyType 抽象基类。

每个内置策略类型都是 StrategyType 的实例（不是子类的"类型"，而是单例）。
约定：
- ``type_key``：全局唯一短标识，落库 pipeline_steps.strategy_type
- ``display_name`` / ``description``：前端展示
- ``param_schema``：JSONSchema（type=object），前端按它自动渲染参数表单
- ``validate_params(params)``：CRUD 写入前校验；非法应抛 ``ValueError``
- ``run(items, params, ctx)``：异步执行；接收 ClassifyBillItem 列表，返回处理后的列表（可原地修改）

引入新的策略类型只需新增一个文件 + 在 ``strategy_types/__init__.py`` 中 register 即可，
前端无需任何改动。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.classify.bill_item import ClassifyBillItem
    from app.classify.context import ClassifyContext


class StrategyType(ABC):
    type_key: str
    display_name: str
    description: str
    param_schema: dict

    def validate_params(self, params: dict) -> None:
        """默认不做校验；子类可覆盖。非法应抛 ValueError(具体原因)"""
        return None

    @abstractmethod
    async def run(
        self,
        items: list["ClassifyBillItem"],
        params: dict,
        ctx: "ClassifyContext",
    ) -> list["ClassifyBillItem"]: ...

    def metadata(self) -> dict:
        return {
            "type_key": self.type_key,
            "display_name": self.display_name,
            "description": self.description,
            "param_schema": self.param_schema,
        }
