"""student default zoom link and birthday

Revision ID: c8d0e2f4a6b8
Revises: a2b4c6d8e0f1
Create Date: 2026-06-12 15:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'c8d0e2f4a6b8'
down_revision: str | None = 'a2b4c6d8e0f1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('students', sa.Column('default_zoom_link', sa.String(length=500), nullable=True))
    op.add_column('students', sa.Column('birthday', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('students', 'birthday')
    op.drop_column('students', 'default_zoom_link')
