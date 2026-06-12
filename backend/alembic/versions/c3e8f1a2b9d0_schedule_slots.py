"""schedule slots

Revision ID: c3e8f1a2b9d0
Revises: 7b12a9f3c4d1
Create Date: 2026-06-12 09:30:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'c3e8f1a2b9d0'
down_revision: str | None = '7b12a9f3c4d1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'schedule_slots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('weekday', sa.SmallInteger(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_slots_student_id'), 'schedule_slots', ['student_id'], unique=False)
    op.add_column('lessons', sa.Column('slot_id', sa.Integer(), nullable=True))
    op.add_column('lessons', sa.Column('slot_date', sa.Date(), nullable=True))
    op.create_foreign_key('fk_lessons_slot_id', 'lessons', 'schedule_slots', ['slot_id'], ['id'])
    op.create_unique_constraint('uq_lessons_slot_occurrence', 'lessons', ['slot_id', 'slot_date'])


def downgrade() -> None:
    op.drop_constraint('uq_lessons_slot_occurrence', 'lessons', type_='unique')
    op.drop_constraint('fk_lessons_slot_id', 'lessons', type_='foreignkey')
    op.drop_column('lessons', 'slot_date')
    op.drop_column('lessons', 'slot_id')
    op.drop_index(op.f('ix_schedule_slots_student_id'), table_name='schedule_slots')
    op.drop_table('schedule_slots')
