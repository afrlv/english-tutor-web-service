import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin


class LessonStatus(str, enum.Enum):
    planned = "planned"
    conducted = "conducted"
    cancelled = "cancelled"


class CancellationKind(str, enum.Enum):
    teacher = "teacher"  # отменил учитель — без оплаты
    student = "student"  # ученик предупредил заранее — без оплаты
    late = "late"  # поздняя отмена / неявка — оплачивается


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
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    # Цена этого урока: NULL — взять с карточки родителя при проведении,
    # 0 — бесплатный (пробный)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    topic: Mapped[str | None] = mapped_column(Text)
    zoom_link: Mapped[str | None] = mapped_column(String(500))
    recommendation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[LessonStatus] = mapped_column(
        Enum(LessonStatus, name="lesson_status"), default=LessonStatus.planned
    )
    conducted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Когда ученику отправлено напоминание (защита от повторной отправки)
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancellation_kind: Mapped[CancellationKind | None] = mapped_column(
        Enum(CancellationKind, name="cancellation_kind")
    )
    cancellation_comment: Mapped[str | None] = mapped_column(Text)
    # Исходное время первого переноса — «урок перенесён с …»
    rescheduled_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    homeworks: Mapped[list["Homework"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", lazy="selectin"
    )


from app.models.homework import Homework  # noqa: E402
