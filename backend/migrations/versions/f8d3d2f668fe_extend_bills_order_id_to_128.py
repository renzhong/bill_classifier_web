"""extend bills.order_id to 128

Revision ID: f8d3d2f668fe
Revises: 0001
Create Date: 2026-06-02 07:26:36.671075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f8d3d2f668fe'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "bills",
        "order_id",
        existing_type=sa.String(length=64),
        type_=sa.String(length=128),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "bills",
        "order_id",
        existing_type=sa.String(length=128),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
