"""multitenancy: students.teacher_id, users.token_version

Revision ID: d2f4b6a8c0e2
Revises: c1a3e5b7d9f2
Create Date: 2026-06-13 11:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'd2f4b6a8c0e2'
down_revision: str | None = 'c1a3e5b7d9f2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('token_version', sa.Integer(), server_default='0', nullable=False),
    )

    # teacher_id: добавляем nullable, бэкофилл единственным учителем, затем NOT NULL
    op.add_column('students', sa.Column('teacher_id', sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE students
        SET teacher_id = (
            SELECT id FROM users WHERE role = 'teacher' ORDER BY id LIMIT 1
        )
        WHERE teacher_id IS NULL
        """
    )
    # Если учеников нет — бэкофиллить нечего; если есть, но учителя нет — это
    # сломанная база, NOT NULL ниже честно упадёт.
    op.alter_column('students', 'teacher_id', nullable=False)
    op.create_index(op.f('ix_students_teacher_id'), 'students', ['teacher_id'], unique=False)
    op.create_foreign_key(
        'fk_students_teacher_id', 'students', 'users', ['teacher_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_students_teacher_id', 'students', type_='foreignkey')
    op.drop_index(op.f('ix_students_teacher_id'), table_name='students')
    op.drop_column('students', 'teacher_id')
    op.drop_column('users', 'token_version')
