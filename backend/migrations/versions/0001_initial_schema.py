"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(128), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nickname", sa.String(64)),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # invitation_codes
    op.create_table(
        "invitation_codes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("used_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("used_at", sa.DateTime),
        sa.Column("expires_at", sa.DateTime),
        sa.Column("max_uses", sa.Integer, nullable=False, server_default="1"),
        sa.Column("used_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_invitation_code"),
    )

    # categories
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(64)),
        sa.Column("color", sa.String(16)),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "name", name="uq_category_user_name"),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"])

    # tags
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("color", sa.String(16)),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
    )
    op.create_index("ix_tags_user_id", "tags", ["user_id"])

    # user_dicts
    op.create_table(
        "user_dicts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("target_field", sa.String(16), nullable=False, server_default="any"),
        sa.Column("remark", sa.String(255)),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "name", name="uq_user_dict_name"),
    )
    op.create_index("ix_user_dicts_user_id", "user_dicts", ["user_id"])

    # user_dict_entries
    op.create_table(
        "user_dict_entries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "dict_id",
            sa.Integer,
            sa.ForeignKey("user_dicts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key_text", sa.String(255), nullable=False),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id"), nullable=False),
    )
    op.create_index("ix_user_dict_entries_dict_id", "user_dict_entries", ["dict_id"])

    # pipeline_steps
    op.create_table(
        "pipeline_steps",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("strategy_type", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("params", sa.JSON, nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_pipeline_steps_user_id", "pipeline_steps", ["user_id"])
    op.create_index("ix_pipeline_steps_sort", "pipeline_steps", ["sort_order"])

    # upload_tasks
    op.create_table(
        "upload_tasks",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("total_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("classified_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_msg", sa.String(1024)),
        sa.Column("tag_ids", sa.JSON, nullable=False),
        sa.Column("owner_label", sa.String(32)),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime),
    )
    op.create_index("ix_upload_tasks_user_id", "upload_tasks", ["user_id"])

    # bills
    op.create_table(
        "bills",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("upload_task_id", sa.BigInteger, sa.ForeignKey("upload_tasks.id")),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("owner", sa.String(32)),
        sa.Column("order_id", sa.String(64)),
        sa.Column("payee", sa.String(255)),
        sa.Column("item_name", sa.String(512)),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("bill_type", sa.String(16), nullable=False, server_default="expense"),
        sa.Column("bill_time", sa.DateTime, nullable=False),
        sa.Column(
            "bill_month",
            sa.String(7),
            sa.Computed("DATE_FORMAT(bill_time, '%Y-%m')", persisted=True),
        ),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id")),
        sa.Column("classify_strategy_id", sa.Integer, sa.ForeignKey("pipeline_steps.id")),
        sa.Column("classify_strategy_type", sa.String(64)),
        sa.Column("lifecycle", sa.String(32), nullable=False, server_default="unprocessed"),
        sa.Column("skip_reason", sa.String(64)),
        sa.Column("group_id", sa.String(64)),
        sa.Column("is_merged", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("merged_from", sa.JSON),
        sa.Column("ai_provider", sa.String(32)),
        sa.Column("ai_confidence", sa.Numeric(3, 2)),
        sa.Column("manual_overridden", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "source", "order_id", name="uk_user_order"),
    )
    op.create_index("idx_user_time", "bills", ["user_id", "bill_time"])
    op.create_index("idx_user_month", "bills", ["user_id", "bill_month"])
    op.create_index("idx_user_cat", "bills", ["user_id", "category_id"])

    # bill_tags
    op.create_table(
        "bill_tags",
        sa.Column("bill_id", sa.BigInteger, sa.ForeignKey("bills.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer, sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_bill_tags_tag_id", "bill_tags", ["tag_id"])

    # ai_credentials
    op.create_table(
        "ai_credentials",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("api_key_encrypted", sa.Text, nullable=False),
        sa.Column("base_url", sa.String(255)),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ai_credentials_user_id", "ai_credentials", ["user_id"])

    # ai_strategies
    op.create_table(
        "ai_strategies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("strategy_text", sa.Text, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("credential_id", sa.Integer, sa.ForeignKey("ai_credentials.id")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_ai_strategies_user_id", "ai_strategies", ["user_id"])

    # monthly_incomes
    op.create_table(
        "monthly_incomes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("year_month", sa.String(7), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("remark", sa.String(255)),
        sa.UniqueConstraint("user_id", "year_month", "source", name="uq_income_user_month_source"),
    )
    op.create_index("ix_monthly_incomes_user_id", "monthly_incomes", ["user_id"])

    # assets
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("snapshot_month", sa.String(7), nullable=False),
        sa.Column("asset_type", sa.String(16), nullable=False),
        sa.Column("account_name", sa.String(64), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("remark", sa.String(255)),
    )
    op.create_index("idx_asset_user_month", "assets", ["user_id", "snapshot_month"])


def downgrade() -> None:
    for tbl in [
        "assets",
        "monthly_incomes",
        "ai_strategies",
        "ai_credentials",
        "bill_tags",
        "bills",
        "upload_tasks",
        "pipeline_steps",
        "user_dict_entries",
        "user_dicts",
        "tags",
        "categories",
        "invitation_codes",
        "users",
    ]:
        op.drop_table(tbl)
