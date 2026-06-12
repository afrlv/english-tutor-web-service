from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class EmailSettingsOut(BaseModel):
    backend: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_from: str
    # Сам пароль наружу не отдаём никогда
    password_set: bool


class EmailSettingsIn(BaseModel):
    backend: Literal["console", "smtp"]
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_from: str = ""
    # None/пустая строка — оставить текущий пароль
    smtp_password: str | None = None


class EmailLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    to_email: str
    subject: str
    status: str
    error: str | None
    created_at: datetime
