from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin


class Homework(Base, CreatedAtMixin):
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str] = mapped_column(Text)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    # Ответ ученика и отметка учителя «проверено» с оценкой 2–5
    student_answer: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    grade: Mapped[int | None] = mapped_column(SmallInteger)

    lesson: Mapped["Lesson"] = relationship(back_populates="homeworks")
    attachments: Mapped[list["HomeworkAttachment"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


from app.models.attachment import HomeworkAttachment  # noqa: E402
from app.models.lesson import Lesson  # noqa: E402
