import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin


class LessonStatus(str, enum.Enum):
    planned = "planned"
    conducted = "conducted"
    cancelled = "cancelled"


class Lesson(Base, CreatedAtMixin):
    __tablename__ = "lessons"
    # Один слот не может породить два урока на одну дату — защита от повторной
    # генерации; перенесённый/отменённый урок сохраняет slot_date и не пересоздаётся
    __table_args__ = (UniqueConstraint("slot_id", "slot_date", name="uq_lessons_slot_occurrence"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    slot_id: Mapped[int | None] = mapped_column(ForeignKey("schedule_slots.id"))
    slot_date: Mapped[date | None] = mapped_column(Date)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    topic: Mapped[str | None] = mapped_column(Text)
    zoom_link: Mapped[str | None] = mapped_column(String(500))
    recommendation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[LessonStatus] = mapped_column(
        Enum(LessonStatus, name="lesson_status"), default=LessonStatus.planned
    )
    conducted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    homeworks: Mapped[list["Homework"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", lazy="selectin"
    )


from app.models.homework import Homework  # noqa: E402
