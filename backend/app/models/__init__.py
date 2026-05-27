"""SQLAlchemy ORM models — 全部导入以便 alembic autogenerate 能发现"""

from app.models.ai import AiCredential, AiStrategy
from app.models.asset import Asset
from app.models.bill import Bill, BillTag, UploadTask
from app.models.category import Category, Tag
from app.models.dict_entry import UserDict, UserDictEntry
from app.models.income import MonthlyIncome
from app.models.invitation import InvitationCode
from app.models.pipeline import PipelineStep
from app.models.user import User

__all__ = [
    "User",
    "InvitationCode",
    "Category",
    "Tag",
    "UserDict",
    "UserDictEntry",
    "PipelineStep",
    "Bill",
    "BillTag",
    "UploadTask",
    "AiCredential",
    "AiStrategy",
    "MonthlyIncome",
    "Asset",
]
