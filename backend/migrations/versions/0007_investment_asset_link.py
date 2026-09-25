"""Optionally replace a manual asset with an investment valuation.

Revision ID: 0007
Revises: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("investment_items", sa.Column("linked_asset_item_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_investment_linked_asset", "investment_items", "asset_items",
                          ["linked_asset_item_id"], ["id"])
    op.create_unique_constraint("uq_investment_linked_asset", "investment_items", ["linked_asset_item_id"])


def downgrade() -> None:
    op.drop_constraint("uq_investment_linked_asset", "investment_items", type_="unique")
    op.drop_constraint("fk_investment_linked_asset", "investment_items", type_="foreignkey")
    op.drop_column("investment_items", "linked_asset_item_id")
