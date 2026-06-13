"""card set optional lesson link

Revision ID: c1a3e5b7d9f2
Revises: b3d5f7a9c1e3
Create Date: 2026-06-13 09:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'c1a3e5b7d9f2'
down_revision: str | None = 'b3d5f7a9c1e3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('card_sets', sa.Column('lesson_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_card_sets_lesson_id'), 'card_sets', ['lesson_id'], unique=False)
    op.create_foreign_key(
        'fk_card_sets_lesson_id', 'card_sets', 'lessons', ['lesson_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_card_sets_lesson_id', 'card_sets', type_='foreignkey')
    op.drop_index(op.f('ix_card_sets_lesson_id'), table_name='card_sets')
    op.drop_column('card_sets', 'lesson_id')
