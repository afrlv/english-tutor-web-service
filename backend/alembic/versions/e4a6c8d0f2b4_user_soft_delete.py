"""user soft delete (deleted_at)

Revision ID: e4a6c8d0f2b4
Revises: d2f4b6a8c0e2
Create Date: 2026-06-13 13:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'e4a6c8d0f2b4'
down_revision: str | None = 'd2f4b6a8c0e2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'deleted_at')
