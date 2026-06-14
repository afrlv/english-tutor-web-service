"""card srs (leitner) + study streak

Revision ID: f7a9c1b3d5e7
Revises: e4a6c8d0f2b4
Create Date: 2026-06-14 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7a9c1b3d5e7"
down_revision: str | None = "e4a6c8d0f2b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Карточки: пример + состояние интервального повторения (Лейтнер)
    op.add_column("cards", sa.Column("example", sa.String(length=500), nullable=True))
    op.add_column(
        "cards",
        sa.Column("box", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "cards", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True)
    )
    # Бэкофилл: бывшие «выученные» (>=2 правильных) сразу в коробку 4; все — в оборот
    op.execute("UPDATE cards SET box = 4 WHERE times_correct >= 2")
    op.execute("UPDATE cards SET due_at = now()")
    op.alter_column("cards", "box", server_default=None)

    # Ученик: серия дней занятий по карточкам
    op.add_column(
        "students",
        sa.Column("study_streak", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "students",
        sa.Column("best_streak", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "students", sa.Column("last_study_date", sa.Date(), nullable=True)
    )
    op.alter_column("students", "study_streak", server_default=None)
    op.alter_column("students", "best_streak", server_default=None)


def downgrade() -> None:
    op.drop_column("students", "last_study_date")
    op.drop_column("students", "best_streak")
    op.drop_column("students", "study_streak")
    op.drop_column("cards", "due_at")
    op.drop_column("cards", "box")
    op.drop_column("cards", "example")
