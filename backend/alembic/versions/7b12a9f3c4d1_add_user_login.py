"""add user login

Revision ID: 7b12a9f3c4d1
Revises: 2c574c805520
Create Date: 2026-06-12 01:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '7b12a9f3c4d1'
down_revision: str | None = '2c574c805520'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('users', sa.Column('login', sa.String(length=255), nullable=True))
    # У существующих пользователей логином становится почта
    op.execute("UPDATE users SET login = email")
    op.alter_column('users', 'login', nullable=False)
    op.create_index(op.f('ix_users_login'), 'users', ['login'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_login'), table_name='users')
    op.drop_column('users', 'login')
