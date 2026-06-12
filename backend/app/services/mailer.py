import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.emails.sender import build_sender
from app.models import EmailLog
from app.services.email_settings import get_email_config

logger = logging.getLogger("app.mailer")


async def send_email(db: AsyncSession, to: str, subject: str, body: str) -> bool:
    """Единая точка отправки: конфиг из БД, результат — в журнал email_log.

    Ошибка отправки не роняет вызывающий сценарий (создание ученика и т.п.) —
    администратор увидит её в журнале. Строка журнала добавляется в сессию,
    коммитит вызывающий.
    """
    cfg = await get_email_config(db)
    sender = build_sender(cfg)
    error: str | None = None
    try:
        await sender.send(to, subject, body)
    except Exception as exc:  # noqa: BLE001 — фиксируем любую ошибку отправки
        logger.exception("Не удалось отправить письмо to=%s", to)
        error = str(exc)[:1000]
    db.add(
        EmailLog(
            to_email=to,
            subject=subject,
            status="error" if error else "sent",
            error=error,
        )
    )
    return error is None
