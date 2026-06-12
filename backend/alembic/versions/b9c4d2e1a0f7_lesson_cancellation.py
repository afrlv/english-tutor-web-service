"""lesson cancellation and reschedule

Revision ID: b9c4d2e1a0f7
Revises: a7b2c3d4e5f6
Create Date: 2026-06-12 10:30:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'b9c4d2e1a0f7'
down_revision: str | None = 'a7b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

cancellation_kind = sa.Enum('teacher', 'student', 'late', name='cancellation_kind')


def upgrade() -> None:
    cancellation_kind.create(op.get_bind())
    op.add_column('lessons', sa.Column('cancellation_kind', cancellation_kind, nullable=True))
    op.add_column('lessons', sa.Column('cancellation_comment', sa.Text(), nullable=True))
    op.add_column('lessons', sa.Column('rescheduled_from', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('lessons', 'rescheduled_from')
    op.drop_column('lessons', 'cancellation_comment')
    op.drop_column('lessons', 'cancellation_kind')
    cancellation_kind.drop(op.get_bind())
