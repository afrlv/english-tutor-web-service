import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.db import async_session
from app.services.digest import send_daily_digest

logger = logging.getLogger("app.scheduler")


async def _digest_job() -> None:
    async with async_session() as db:
        await send_daily_digest(db)


def create_scheduler() -> AsyncIOScheduler:
    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone=settings.tz)
    scheduler.add_job(
        _digest_job,
        CronTrigger(hour=settings.digest_hour, minute=0, timezone=settings.tz),
        id="daily_digest",
    )
    logger.info("Дайджест запланирован ежедневно на %02d:00 (%s)", settings.digest_hour, settings.tz)
    return scheduler
