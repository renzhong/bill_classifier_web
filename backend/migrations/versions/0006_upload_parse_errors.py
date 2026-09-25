"""Store failed row descriptions for upload preview.

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("upload_tasks", sa.Column("parse_errors", sa.JSON(), nullable=True))
    op.execute("UPDATE upload_tasks SET parse_errors = JSON_ARRAY() WHERE parse_errors IS NULL")
    op.alter_column("upload_tasks", "parse_errors", existing_type=sa.JSON(), nullable=False)


def downgrade() -> None:
    op.drop_column("upload_tasks", "parse_errors")
