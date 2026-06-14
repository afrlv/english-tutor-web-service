from datetime import datetime, timedelta

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin


class CardSet(Base, CreatedAtMixin):
    """Набор карточек «слово – перевод» для ученика.

    lesson_id — необязательная привязка к уроку (слова конкретного занятия);
    при удалении урока набор остаётся у ученика (SET NULL).
    """

    __tablename__ = "card_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    lesson_id: Mapped[int | None] = mapped_column(
        ForeignKey("lessons.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))

    cards: Mapped[list["Card"]] = relationship(
        back_populates="card_set",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Card.position",
    )


class Card(Base, CreatedAtMixin):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    set_id: Mapped[int] = mapped_column(
        ForeignKey("card_sets.id", ondelete="CASCADE"), index=True
    )
    front: Mapped[str] = mapped_column(String(500))  # слово/фраза
    back: Mapped[str] = mapped_column(String(500))  # перевод
    example: Mapped[str | None] = mapped_column(String(500))  # пример употребления
    position: Mapped[int] = mapped_column(Integer, default=0)
    # Интервальное повторение (Лейтнер): коробка 0 = новая/в изучении, выше = реже.
    box: Mapped[int] = mapped_column(Integer, default=0)
    # Когда карточка снова к повтору; NULL = новая, показываем сразу.
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Накопительная статистика ответов (для учителя); SRS-логику ведёт box/due_at.
    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    times_wrong: Mapped[int] = mapped_column(Integer, default=0)

    card_set: Mapped[CardSet] = relationship(back_populates="cards")


# Интервалы повтора (в днях) для коробок 1..MAX_BOX. Ответ верно поднимает на коробку
# выше и откладывает повтор на следующий интервал; ошибка опускает на коробку ниже.
BOX_INTERVALS = [1, 2, 4, 8, 16, 32]
MAX_BOX = len(BOX_INTERVALS)  # = 6
# Карточка «выучена», когда пережила интервал коробки 4 (~неделя) и выше.
LEARNED_BOX = 4


def apply_answer(card: Card, correct: bool, now: datetime) -> None:
    """Обновляет состояние карточки по ответу ученика (Лейтнер)."""
    if correct:
        card.box = min(card.box + 1, MAX_BOX)
        card.times_correct += 1
        card.due_at = now + timedelta(days=BOX_INTERVALS[card.box - 1])
    else:
        card.box = max(card.box - 1, 0)
        card.times_wrong += 1
        card.due_at = now  # вернуть в оборот сегодня же


def is_due(card: Card, now: datetime) -> bool:
    return card.due_at is None or card.due_at <= now
