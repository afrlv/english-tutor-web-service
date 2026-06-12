"""card sets (flashcards)

Revision ID: f5b7d9e1a3c5
Revises: e9f1a3b5c7d9
Create Date: 2026-06-12 17:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'f5b7d9e1a3c5'
down_revision: str | None = 'e9f1a3b5c7d9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'card_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_card_sets_student_id'), 'card_sets', ['student_id'], unique=False)
    op.create_table(
        'cards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('set_id', sa.Integer(), nullable=False),
        sa.Column('front', sa.String(length=500), nullable=False),
        sa.Column('back', sa.String(length=500), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('times_correct', sa.Integer(), nullable=False),
        sa.Column('times_wrong', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['set_id'], ['card_sets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_cards_set_id'), 'cards', ['set_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_cards_set_id'), table_name='cards')
    op.drop_table('cards')
    op.drop_index(op.f('ix_card_sets_student_id'), table_name='card_sets')
    op.drop_table('card_sets')
