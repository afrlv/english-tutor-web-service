from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.emails.sender import EmailConfig
from app.models import EmailSettings

SINGLETON_ID = 1


async def get_email_config(db: AsyncSession) -> EmailConfig:
    """Действующая конфигурация почты: строка в БД важнее env-значений."""
    row = await db.get(EmailSettings, SINGLETON_ID)
    if row is not None:
        return EmailConfig(
            backend=row.backend,
            smtp_host=row.smtp_host,
            smtp_port=row.smtp_port,
            smtp_user=row.smtp_user,
            smtp_password=row.smtp_password,
            smtp_from=row.smtp_from,
        )
    s = get_settings()
    return EmailConfig(
        backend=s.email_backend,
        smtp_host=s.smtp_host,
        smtp_port=s.smtp_port,
        smtp_user=s.smtp_user,
        smtp_password=s.smtp_password,
        smtp_from=s.smtp_from,
    )


async def get_or_create_row(db: AsyncSession) -> EmailSettings:
    row = await db.get(EmailSettings, SINGLETON_ID)
    if row is None:
        cfg = await get_email_config(db)  # стартуем с env-значений
        row = EmailSettings(
            id=SINGLETON_ID,
            backend=cfg.backend,
            smtp_host=cfg.smtp_host,
            smtp_port=cfg.smtp_port,
            smtp_user=cfg.smtp_user,
            smtp_password=cfg.smtp_password,
            smtp_from=cfg.smtp_from,
        )
        db.add(row)
        await db.flush()
    return row
