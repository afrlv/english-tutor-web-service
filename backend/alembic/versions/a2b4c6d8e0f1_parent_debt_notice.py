"""parent debt notice timestamp

Revision ID: a2b4c6d8e0f1
Revises: f1e3c5a7b9d2
Create Date: 2026-06-12 14:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'a2b4c6d8e0f1'
down_revision: str | None = 'f1e3c5a7b9d2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'parents',
        sa.Column('debt_notice_sent_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('parents', 'debt_notice_sent_at')
