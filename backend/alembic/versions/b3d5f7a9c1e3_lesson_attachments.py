"""lesson attachments (materials)

Revision ID: b3d5f7a9c1e3
Revises: f5b7d9e1a3c5
Create Date: 2026-06-12 18:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'b3d5f7a9c1e3'
down_revision: str | None = 'f5b7d9e1a3c5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'lesson_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=True),
        sa.Column('url', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_lesson_attachments_lesson_id'), 'lesson_attachments', ['lesson_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_lesson_attachments_lesson_id'), table_name='lesson_attachments')
    op.drop_table('lesson_attachments')
