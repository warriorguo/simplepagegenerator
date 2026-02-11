"""add kv_cache table

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-02-11 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'kv_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cache_key', sa.String(255), nullable=False),
        sa.Column('value_text', sa.Text(), nullable=False),
        sa.Column('meta_json', JSONB(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_kv_cache_cache_key', 'kv_cache', ['cache_key'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_kv_cache_cache_key', table_name='kv_cache')
    op.drop_table('kv_cache')
