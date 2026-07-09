"""parent → multiple children: drop unique on parents.user_id

Revision ID: a1c3e5b7d9f0
Revises: f7a9c1b3d5e7
Create Date: 2026-06-14 22:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

revision: str = "a1c3e5b7d9f0"
down_revision: str | None = "f7a9c1b3d5e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Один родитель может иметь несколько карточек (по одной на ребёнка):
    # снимаем UNIQUE с user_id, оставляем обычный индекс. student_id UNIQUE не трогаем.
    op.drop_constraint("parents_user_id_key", "parents", type_="unique")
    op.create_index("ix_parents_user_id", "parents", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_parents_user_id", table_name="parents")
    op.create_unique_constraint("parents_user_id_key", "parents", ["user_id"])
