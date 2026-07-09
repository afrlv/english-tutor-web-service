from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin
from app.models.user import User


class Parent(Base, CreatedAtMixin):
    __tablename__ = "parents"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Один родитель (user) может иметь несколько карточек — по одной на ребёнка
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # Одна карточка родителя на ученика — леджер однозначно знает цену урока
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), unique=True)
    lesson_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    recommendations: Mapped[str | None] = mapped_column(Text)
    # Когда отправлено последнее напоминание о долге (сбрасывается при погашении)
    debt_notice_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(lazy="joined")
