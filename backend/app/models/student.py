from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin
from app.models.user import User


class Student(Base, CreatedAtMixin):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    # Виден только учителю и суперюзеру: не включается в схемы ученика/родителя
    teacher_private_note: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(lazy="joined")
