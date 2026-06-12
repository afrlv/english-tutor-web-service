from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin


class HomeworkAttachment(Base, CreatedAtMixin):
    """Вложение к ДЗ: загруженный файл (file_path) или внешняя ссылка (url)."""

    __tablename__ = "homework_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    homework_id: Mapped[int] = mapped_column(
        ForeignKey("homeworks.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))  # имя файла или подпись ссылки
    file_path: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(1000))


class LessonAttachment(Base, CreatedAtMixin):
    """Материал урока: файл или ссылка на уровне урока (не ДЗ)."""

    __tablename__ = "lesson_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(1000))
