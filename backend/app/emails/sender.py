from typing import Protocol

from app.config import get_settings


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


def get_email_sender() -> EmailSender:
    settings = get_settings()
    if settings.email_backend == "console":
        from app.emails.console import ConsoleEmailSender

        return ConsoleEmailSender()
    raise ValueError(f"Неизвестный email-бэкенд: {settings.email_backend}")
