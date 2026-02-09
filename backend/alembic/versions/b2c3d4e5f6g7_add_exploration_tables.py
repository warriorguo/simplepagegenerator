"""add exploration tables

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-09 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Exploration sessions
    op.create_table(
        'exploration_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_input', sa.Text(), nullable=False),
        sa.Column('ambiguity_json', JSONB(), nullable=True),
        sa.Column('state', sa.String(30), nullable=False, server_default='explore_options'),
        sa.Column('selected_option_id', sa.String(100), nullable=True),
        sa.Column('hypothesis_ledger', JSONB(), nullable=True),
        sa.Column('iteration_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )

    # Exploration options
    op.create_table(
        'exploration_options',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('option_id', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('core_loop', sa.Text(), nullable=False),
        sa.Column('controls', sa.String(255), nullable=False),
        sa.Column('mechanics', JSONB(), nullable=False),
        sa.Column('template_id', sa.String(100), nullable=False),
        sa.Column('complexity', sa.String(20), nullable=False),
        sa.Column('mobile_fit', sa.String(20), nullable=False),
        sa.Column('assumptions_to_validate', JSONB(), nullable=True),
        sa.Column('is_recommended', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['exploration_sessions.id'], ondelete='CASCADE'),
    )

    # Exploration memory notes
    op.create_table(
        'exploration_memory_notes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),
        sa.Column('content_json', JSONB(), nullable=False),
        sa.Column('tags', JSONB(), nullable=True),
        sa.Column('confidence', sa.Float(), server_default='0.8'),
        sa.Column('source_version_id', sa.Integer(), nullable=True),
        sa.Column('source_session_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_session_id'], ['exploration_sessions.id'], ondelete='SET NULL'),
    )

    # User preferences
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),
        sa.Column('preference_json', JSONB(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('user_preferences')
    op.drop_table('exploration_memory_notes')
    op.drop_table('exploration_options')
    op.drop_table('exploration_sessions')
