"""Initial schema — all core tables

Revision ID: 001_initial
Revises:
Create Date: 2026-04-21

SQLite-compatible: uses String instead of native Enum types.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Inbox items (Capture Engine) ──────────────────────────────────────────
    op.create_table(
        "inbox_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("item_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("clarified_as", sa.String(50), nullable=True),
        sa.Column("clarified_ref_id", sa.String(36), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
    )

    # ── Projects ──────────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("area", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── Tasks ─────────────────────────────────────────────────────────────────
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="next"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("context", sa.String(100), nullable=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("estimated_time", sa.Integer(), nullable=True),
        sa.Column("actual_time", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── Task Events (Event System) ────────────────────────────────────────────
    op.create_table(
        "task_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── Decision Logs (Thinking Engine) ───────────────────────────────────────
    op.create_table(
        "decision_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("log_type", sa.String(30), nullable=False, server_default="decision"),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("hypotheses", sa.Text(), nullable=True),
        sa.Column("options", sa.Text(), nullable=True),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("expected_outcome", sa.Text(), nullable=True),
        sa.Column("actual_outcome", sa.Text(), nullable=True),
        sa.Column("markdown_path", sa.String(1000), nullable=True),
        sa.Column("tags", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── Notes (Knowledge System / PARA) ───────────────────────────────────────
    op.create_table(
        "notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("category", sa.String(20), nullable=False, server_default="resource"),
        sa.Column("tags", sa.String(500), nullable=True),
        sa.Column("markdown_path", sa.String(1000), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("linked_note_ids", sa.String(2000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    op.create_index("ix_inbox_status", "inbox_items", ["status"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"])
    op.create_index("ix_tasks_context", "tasks", ["context"])
    op.create_index("ix_events_task_id", "task_events", ["task_id"])
    op.create_index("ix_events_type", "task_events", ["event_type"])
    op.create_index("ix_notes_category", "notes", ["category"])


def downgrade() -> None:
    op.drop_index("ix_notes_category")
    op.drop_index("ix_events_type")
    op.drop_index("ix_events_task_id")
    op.drop_index("ix_tasks_context")
    op.drop_index("ix_tasks_project_id")
    op.drop_index("ix_tasks_status")
    op.drop_index("ix_inbox_status")
    op.drop_table("notes")
    op.drop_table("decision_logs")
    op.drop_table("task_events")
    op.drop_table("tasks")
    op.drop_table("projects")
    op.drop_table("inbox_items")
