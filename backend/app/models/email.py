from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin


class EmailSettings(Base):
    """Настройки отправки почты (синглтон id=1). Приоритет над env-значениями."""

    __tablename__ = "email_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    backend: Mapped[str] = mapped_column(String(20), default="console")
    smtp_host: Mapped[str] = mapped_column(String(255), default="")
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_user: Mapped[str] = mapped_column(String(255), default="")
    smtp_password: Mapped[str] = mapped_column(String(255), default="")
    smtp_from: Mapped[str] = mapped_column(String(255), default="")


class EmailLog(Base, CreatedAtMixin):
    """Журнал отправки писем: что, кому, успех/ошибка."""

    __tablename__ = "email_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    to_email: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(10))  # sent | error
    error: Mapped[str | None] = mapped_column(Text)
