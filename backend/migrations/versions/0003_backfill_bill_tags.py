"""backfill bill tags selected at upload

Revision ID: 0003
Revises: f8d3d2f668fe
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "f8d3d2f668fe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add valid upload tags without removing existing bill tags.
    op.execute(sa.text("""
        INSERT INTO bill_tags (bill_id, tag_id)
        SELECT DISTINCT b.id, tag.id
        FROM bills AS b
        JOIN upload_tasks AS task ON task.id = b.upload_task_id
            AND task.user_id = b.user_id
        JOIN JSON_TABLE(
            COALESCE(task.tag_ids, JSON_ARRAY()),
            '$[*]' COLUMNS (tag_id INT PATH '$')
        ) AS selected_tag
        JOIN tags AS tag ON tag.id = selected_tag.tag_id
            AND tag.user_id = b.user_id
        WHERE NOT EXISTS (
            SELECT 1 FROM bill_tags AS existing
            WHERE existing.bill_id = b.id AND existing.tag_id = tag.id
        )
    """))


def downgrade() -> None:
    # Historical associations cannot be distinguished from later manual edits.
    pass
