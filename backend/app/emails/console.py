import logging

logger = logging.getLogger("app.emails")


class ConsoleEmailSender:
    """Заглушка: пишет письма в лог. Реальный SMTP подключается новым классом + env."""

    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info("EMAIL to=%s subject=%s\n%s", to, subject, body)
