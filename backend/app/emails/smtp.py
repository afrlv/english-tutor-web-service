import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import Settings

logger = logging.getLogger("app.emails")


class SmtpEmailSender:
    """Отправка через SMTP (Gmail/Яндекс с паролем приложения и т.п.).

    Порт 465 — implicit TLS, иначе STARTTLS.
    """

    def __init__(self, settings: Settings):
        self._settings = settings

    async def send(self, to: str, subject: str, body: str) -> None:
        s = self._settings
        msg = EmailMessage()
        msg["From"] = s.smtp_from or s.smtp_user
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        await aiosmtplib.send(
            msg,
            hostname=s.smtp_host,
            port=s.smtp_port,
            username=s.smtp_user or None,
            password=s.smtp_password or None,
            use_tls=s.smtp_port == 465,
            start_tls=None if s.smtp_port == 465 else True,
        )
        logger.info("EMAIL отправлен через SMTP to=%s subject=%s", to, subject)
