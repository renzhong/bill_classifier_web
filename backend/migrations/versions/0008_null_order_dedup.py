"""Deduplicate concurrent imports without transaction order IDs.

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bills", sa.Column("dedup_hash", sa.String(64), nullable=True))
    op.create_unique_constraint("uq_bill_null_order_hash", "bills", ["user_id", "source", "dedup_hash"])


def downgrade() -> None:
    op.drop_constraint("uq_bill_null_order_hash", "bills", type_="unique")
    op.drop_column("bills", "dedup_hash")
