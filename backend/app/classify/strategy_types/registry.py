"""StrategyType 注册器：进程启动时由 strategy_types/__init__.py 调用 register()"""
from __future__ import annotations

from app.classify.strategy_types.base import StrategyType

REGISTRY: dict[str, StrategyType] = {}


def register(strategy: StrategyType) -> None:
    if strategy.type_key in REGISTRY:
        raise RuntimeError(f"StrategyType {strategy.type_key!r} already registered")
    REGISTRY[strategy.type_key] = strategy


def get(type_key: str) -> StrategyType | None:
    return REGISTRY.get(type_key)


def registered_types() -> list[StrategyType]:
    return list(REGISTRY.values())
