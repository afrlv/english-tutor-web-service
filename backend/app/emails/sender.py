from dataclasses import dataclass
from typing import Protocol


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


@dataclass
class EmailConfig:
    backend: str = "console"  # console | smtp
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""


def build_sender(cfg: EmailConfig) -> EmailSender:
    if cfg.backend == "smtp":
        from app.emails.smtp import SmtpEmailSender

        return SmtpEmailSender(cfg)
    if cfg.backend == "console":
        from app.emails.console import ConsoleEmailSender

        return ConsoleEmailSender()
    raise ValueError(f"Неизвестный email-бэкенд: {cfg.backend}")
