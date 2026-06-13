from sqlalchemy import ForeignKey, Integer, String
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
    position: Mapped[int] = mapped_column(Integer, default=0)
    # Счётчики ответов ученика; карточка «выучена» при times_correct >= LEARNED_THRESHOLD
    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    times_wrong: Mapped[int] = mapped_column(Integer, default=0)

    card_set: Mapped[CardSet] = relationship(back_populates="cards")


# Сколько правильных ответов делает карточку «выученной»
LEARNED_THRESHOLD = 2
