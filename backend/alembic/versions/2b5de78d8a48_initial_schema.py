"""initial schema

Revision ID: 2b5de78d8a48
Revises:
Create Date: 2026-02-08 15:53:47.193815
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2b5de78d8a48'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old projects table columns if they exist, add new ones
    # First check if the old 'projects' table has our columns already
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Handle projects table - drop old one if it exists with different schema
    if 'projects' in existing_tables:
        existing_cols = {c['name'] for c in inspector.get_columns('projects')}
        if 'title' not in existing_cols:
            # Old projects table from another app - drop and recreate
            # First drop any dependent objects
            try:
                op.drop_index('idx_projects_created_at', table_name='projects')
            except Exception:
                pass
            try:
                op.drop_index('idx_projects_deleted_at', table_name='projects')
            except Exception:
                pass
            # Drop documents table FK if exists
            if 'documents' in existing_tables:
                op.drop_table('documents')
            op.drop_table('projects')

    # Create projects table
    if 'projects' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('projects',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
            sa.Column('current_version_id', sa.Integer(), nullable=True),
            sa.Column('published_version_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )

    # Create chat_threads
    op.create_table('chat_threads',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id')
    )

    # Create chat_messages
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['thread_id'], ['chat_threads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create project_versions
    op.create_table('project_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('source_message_id', sa.Integer(), nullable=True),
        sa.Column('build_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('build_log', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add deferred FK for source_message_id
    op.create_foreign_key(
        'fk_version_source_message', 'project_versions', 'chat_messages',
        ['source_message_id'], ['id']
    )

    # Create project_files
    op.create_table('project_files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['version_id'], ['project_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add FKs from projects to project_versions
    op.create_foreign_key(
        'fk_project_current_version', 'projects', 'project_versions',
        ['current_version_id'], ['id']
    )
    op.create_foreign_key(
        'fk_project_published_version', 'projects', 'project_versions',
        ['published_version_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_project_published_version', 'projects', type_='foreignkey')
    op.drop_constraint('fk_project_current_version', 'projects', type_='foreignkey')
    op.drop_table('project_files')
    op.drop_constraint('fk_version_source_message', 'project_versions', type_='foreignkey')
    op.drop_table('project_versions')
    op.drop_table('chat_messages')
    op.drop_table('chat_threads')
    op.drop_table('projects')
