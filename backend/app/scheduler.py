import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.db import async_session
from app.services.digest import send_daily_digest
from app.services.reminders import send_lesson_reminders
from app.services.schedule import generate_all

logger = logging.getLogger("app.scheduler")


async def _digest_job() -> None:
    async with async_session() as db:
        await send_daily_digest(db)


async def _generate_job() -> None:
    async with async_session() as db:
        await generate_all(db)


async def _reminders_job() -> None:
    async with async_session() as db:
        await send_lesson_reminders(db)


def create_scheduler() -> AsyncIOScheduler:
    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone=settings.tz)
    scheduler.add_job(
        _digest_job,
        CronTrigger(hour=settings.digest_hour, minute=0, timezone=settings.tz),
        id="daily_digest",
    )
    # Ночная подгенерация уроков из слотов + сразу при старте (после простоя)
    scheduler.add_job(
        _generate_job,
        CronTrigger(hour=3, minute=0, timezone=settings.tz),
        id="generate_lessons",
    )
    scheduler.add_job(_generate_job, id="generate_lessons_startup")
    # Напоминания ученикам о ближайших уроках
    scheduler.add_job(
        _reminders_job, IntervalTrigger(minutes=15), id="lesson_reminders"
    )
    logger.info("Дайджест запланирован ежедневно на %02d:00 (%s)", settings.digest_hour, settings.tz)
    return scheduler
