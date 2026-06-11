from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin
from app.models.user import User


class Parent(Base, CreatedAtMixin):
    __tablename__ = "parents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    # Одна карточка родителя на ученика — леджер однозначно знает цену урока
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), unique=True)
    lesson_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    recommendations: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(lazy="joined")
