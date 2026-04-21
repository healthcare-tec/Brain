"""Add tags, recurrence, reminder fields to tasks

Revision ID: 002_tags_recurrence
Revises: 001_initial
Create Date: 2026-04-21

SQLite-compatible: uses batch mode for ALTER TABLE.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_tags_recurrence"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("tags", sa.String(1000), nullable=True))
        batch_op.add_column(sa.Column("recurrence", sa.String(20), nullable=False, server_default="none"))
        batch_op.add_column(sa.Column("recurrence_interval", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("parent_task_id", sa.String(36), nullable=True))
        batch_op.add_column(sa.Column("reminder_at", sa.DateTime(), nullable=True))

    op.create_index("ix_tasks_tags", "tasks", ["tags"])
    op.create_index("ix_tasks_reminder", "tasks", ["reminder_at"])


def downgrade() -> None:
    op.drop_index("ix_tasks_reminder")
    op.drop_index("ix_tasks_tags")
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("reminder_at")
        batch_op.drop_column("parent_task_id")
        batch_op.drop_column("recurrence_interval")
        batch_op.drop_column("recurrence")
        batch_op.drop_column("tags")
