"""lesson duration and price

Revision ID: f1e3c5a7b9d2
Revises: d4f6a8b0c2e1
Create Date: 2026-06-12 13:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'f1e3c5a7b9d2'
down_revision: str | None = 'd4f6a8b0c2e1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'lessons',
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='60'),
    )
    op.add_column('lessons', sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column('lessons', 'price')
    op.drop_column('lessons', 'duration_minutes')
