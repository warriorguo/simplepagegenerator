"""add project_memories table

Revision ID: a1b2c3d4e5f6
Revises: 2b5de78d8a48
Create Date: 2026-02-08 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '2b5de78d8a48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute("""
        CREATE TABLE project_memories (
            id SERIAL PRIMARY KEY,
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            embedding vector(1536),
            source VARCHAR(20) NOT NULL DEFAULT 'auto',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute(
        "CREATE INDEX ix_project_memories_embedding ON project_memories "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS project_memories")
