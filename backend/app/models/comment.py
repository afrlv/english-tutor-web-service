from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin
from app.models.user import User


class StudentComment(Base, CreatedAtMixin):
    """Комментарии в карточке ученика: пишут ученик и учитель, родителю не видны."""

    __tablename__ = "student_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)

    author: Mapped[User] = relationship(lazy="joined")
