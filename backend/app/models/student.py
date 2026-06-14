from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin
from app.models.user import User


class Student(Base, CreatedAtMixin):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    # Арендатор: учитель-владелец. Ученик принадлежит ровно одному учителю
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # Виден только учителю и суперюзеру: не включается в схемы ученика/родителя
    teacher_private_note: Mapped[str | None] = mapped_column(Text)
    # Постоянная zoom-ссылка: подставляется в новые уроки без своей ссылки
    default_zoom_link: Mapped[str | None] = mapped_column(String(500))
    birthday: Mapped[date | None] = mapped_column(Date)
    # Серия дней подряд с занятиями по карточкам (мотивация); считается при ответе.
    study_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_study_date: Mapped[date | None] = mapped_column(Date)

    user: Mapped[User] = relationship(lazy="joined", foreign_keys=[user_id])
