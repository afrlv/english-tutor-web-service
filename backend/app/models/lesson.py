import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin


class LessonStatus(str, enum.Enum):
    planned = "planned"
    conducted = "conducted"
    cancelled = "cancelled"


class Lesson(Base, CreatedAtMixin):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
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
