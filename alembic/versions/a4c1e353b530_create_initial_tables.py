"""create initial tables

Revision ID: a4c1e353b530
Revises: 
Create Date: 2026-04-24 16:40:50.629401
"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = 'a4c1e353b530'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index("ix_chat_sessions_id", "chat_sessions", ["id"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_documents_id", "documents", ["id"], unique=False)
    op.create_index("ix_documents_filename", "documents", ["filename"], unique=True)

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("chat_sessions.id"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_messages_id", "chat_messages", ["id"], unique=False)
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_id", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_documents_filename", table_name="documents")
    op.drop_index("ix_documents_id", table_name="documents")
    op.drop_table("documents")

    op.drop_index("ix_chat_sessions_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")
