"""Add staged bills and reusable monthly finance records.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bills", sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.text("0")))
    op.create_index("ix_bills_archived", "bills", ["archived"])
    bind = op.get_bind()
    bind.execute(sa.text("UPDATE bills SET archived = 1"))
    bind.execute(sa.text("UPDATE upload_tasks SET status = 'archived' WHERE status = 'done'"))

    op.create_table(
        "asset_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("legacy_type", sa.String(16)),
        sa.UniqueConstraint("user_id", "kind", "name", name="uq_asset_item_name"),
    )
    op.create_index("ix_asset_items_user_id", "asset_items", ["user_id"])
    op.create_table(
        "asset_month_values",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("asset_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("remark", sa.String(255)),
        sa.UniqueConstraint("item_id", "month", name="uq_asset_item_month"),
    )
    op.create_index("ix_asset_month_values_item_id", "asset_month_values", ["item_id"])
    op.create_table(
        "investment_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("initial_principal", sa.Numeric(14, 2), nullable=False),
        sa.Column("first_month", sa.String(7), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.UniqueConstraint("user_id", "name", name="uq_investment_name"),
    )
    op.create_index("ix_investment_items_user_id", "investment_items", ["user_id"])
    op.create_table(
        "investment_months",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("investment_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("buys", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("sells", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("closing_value", sa.Numeric(14, 2)),
        sa.UniqueConstraint("item_id", "month", name="uq_investment_month"),
    )
    op.create_index("ix_investment_months_item_id", "investment_months", ["item_id"])
    op.create_table(
        "income_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("source", sa.String(64)),
        sa.Column("remark", sa.String(255)),
    )
    op.create_index("ix_income_entries_user_id", "income_entries", ["user_id"])
    op.create_index("ix_income_entries_occurred_at", "income_entries", ["occurred_at"])

    # Original rows stay intact. Reconcile repeated same-name/month snapshots by sum.
    legacy = bind.execute(sa.text(
        "SELECT user_id, asset_type, account_name, snapshot_month, SUM(amount) amount "
        "FROM assets GROUP BY user_id, asset_type, account_name, snapshot_month "
        "ORDER BY user_id, asset_type, account_name, snapshot_month"
    )).mappings().all()
    item_ids: dict[tuple[int, str, str], int] = {}
    used_names: set[tuple[int, str]] = set()
    for row in legacy:
        key = (row["user_id"], row["asset_type"], row["account_name"])
        if key not in item_ids:
            base = row["account_name"][:64]
            name = base
            suffix = 2
            while (row["user_id"], name) in used_names:
                tail = f" ({row['asset_type']} {suffix})"
                name = base[:64 - len(tail)] + tail
                suffix += 1
            used_names.add((row["user_id"], name))
            result = bind.execute(sa.text(
                "INSERT INTO asset_items (user_id, name, kind, active, legacy_type) "
                "VALUES (:user_id, :name, 'asset', 1, :legacy_type)"
            ), {"user_id": row["user_id"], "name": name, "legacy_type": row["asset_type"]})
            item_ids[key] = result.lastrowid
        bind.execute(sa.text(
            "INSERT INTO asset_month_values (item_id, month, amount) "
            "VALUES (:item_id, :month, :amount)"
        ), {"item_id": item_ids[key], "month": row["snapshot_month"], "amount": row["amount"]})


def downgrade() -> None:
    op.drop_index("ix_income_entries_occurred_at", table_name="income_entries")
    op.drop_index("ix_income_entries_user_id", table_name="income_entries")
    op.drop_table("income_entries")
    op.drop_index("ix_investment_months_item_id", table_name="investment_months")
    op.drop_table("investment_months")
    op.drop_index("ix_investment_items_user_id", table_name="investment_items")
    op.drop_table("investment_items")
    op.drop_index("ix_asset_month_values_item_id", table_name="asset_month_values")
    op.drop_table("asset_month_values")
    op.drop_index("ix_asset_items_user_id", table_name="asset_items")
    op.drop_table("asset_items")
    op.drop_index("ix_bills_archived", table_name="bills")
    op.drop_column("bills", "archived")
