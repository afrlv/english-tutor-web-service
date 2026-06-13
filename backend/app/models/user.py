import enum

from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin


class Role(str, enum.Enum):
    superuser = "superuser"
    teacher = "teacher"
    student = "student"
    parent = "parent"


class User(Base, CreatedAtMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Отдельный логин для входа (по умолчанию равен почте); вход работает по обоим
    login: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"))
    avatar_path: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Версия токена: инкремент инвалидирует все ранее выданные JWT
    token_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
