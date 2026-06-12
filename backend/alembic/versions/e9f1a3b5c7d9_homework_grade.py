"""homework grade

Revision ID: e9f1a3b5c7d9
Revises: c8d0e2f4a6b8
Create Date: 2026-06-12 16:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'e9f1a3b5c7d9'
down_revision: str | None = 'c8d0e2f4a6b8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('homeworks', sa.Column('grade', sa.SmallInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('homeworks', 'grade')
