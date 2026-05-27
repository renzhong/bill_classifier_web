"""注册全部内置 StrategyType。

MVP 只内置 ai_classify；其他类型按需后续单独迭代，不主动补充。
"""
from app.classify.strategy_types.ai_classify import AiClassifyStrategy
from app.classify.strategy_types.base import StrategyType
from app.classify.strategy_types.registry import REGISTRY, register, registered_types

register(AiClassifyStrategy())

__all__ = ["StrategyType", "REGISTRY", "register", "registered_types"]
