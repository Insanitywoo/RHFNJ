"""add indexing tasks

Revision ID: b9d4f1c2a001
Revises: a4c1e353b530
Create Date: 2026-04-24 17:10:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "b9d4f1c2a001"
down_revision = "a4c1e353b530"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "indexing_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_indexing_tasks_id", "indexing_tasks", ["id"], unique=False)
    op.create_index("ix_indexing_tasks_document_id", "indexing_tasks", ["document_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_indexing_tasks_document_id", table_name="indexing_tasks")
    op.drop_index("ix_indexing_tasks_id", table_name="indexing_tasks")
    op.drop_table("indexing_tasks")
