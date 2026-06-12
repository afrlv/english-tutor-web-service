"""lesson reminder sent

Revision ID: e5d7a8c1f2b3
Revises: c3e8f1a2b9d0
Create Date: 2026-06-12 11:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'e5d7a8c1f2b3'
down_revision: str | None = 'c3e8f1a2b9d0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'lessons',
        sa.Column('reminder_sent_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('lessons', 'reminder_sent_at')
