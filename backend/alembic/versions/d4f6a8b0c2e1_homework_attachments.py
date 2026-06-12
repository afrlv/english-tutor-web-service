"""homework attachments, answer, checked

Revision ID: d4f6a8b0c2e1
Revises: b9c4d2e1a0f7
Create Date: 2026-06-12 12:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'd4f6a8b0c2e1'
down_revision: str | None = 'b9c4d2e1a0f7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'homework_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('homework_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=True),
        sa.Column('url', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['homework_id'], ['homeworks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_homework_attachments_homework_id'), 'homework_attachments', ['homework_id'], unique=False)
    op.add_column('homeworks', sa.Column('student_answer', sa.Text(), nullable=True))
    op.add_column('homeworks', sa.Column('checked_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('homeworks', 'checked_at')
    op.drop_column('homeworks', 'student_answer')
    op.drop_index(op.f('ix_homework_attachments_homework_id'), table_name='homework_attachments')
    op.drop_table('homework_attachments')
