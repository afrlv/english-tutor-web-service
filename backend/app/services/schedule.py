import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Lesson, LessonStatus, ScheduleSlot

logger = logging.getLogger("app.schedule")


async def generate_lessons_for_slot(db: AsyncSession, slot: ScheduleSlot) -> int:
    """Материализует уроки слота на generate_weeks вперёд. Идемпотентно.

    Урок не создаётся, если на эту дату слота уже есть урок (даже перенесённый
    на другое время или отменённый) — индивидуальные правки серия не трогает.
    Не коммитит — это делает вызывающий.
    """
    settings = get_settings()
    tz = ZoneInfo(settings.tz)
    now = datetime.now(tz)
    horizon = now.date() + timedelta(weeks=settings.generate_weeks)

    existing_dates = set(
        (
            await db.scalars(
                select(Lesson.slot_date).where(Lesson.slot_id == slot.id)
            )
        ).all()
    )

    day = now.date() + timedelta(days=(slot.weekday - now.date().weekday()) % 7)
    created = 0
    while day < horizon:
        scheduled_at = datetime.combine(day, slot.start_time, tzinfo=tz)
        if scheduled_at > now and day not in existing_dates:
            db.add(
                Lesson(
                    student_id=slot.student_id,
                    scheduled_at=scheduled_at,
                    slot_id=slot.id,
                    slot_date=day,
                )
            )
            created += 1
        day += timedelta(days=7)
    return created


async def generate_all(db: AsyncSession) -> int:
    """Ежедневная подгенерация горизонта по всем активным слотам."""
    slots = (
        await db.scalars(select(ScheduleSlot).where(ScheduleSlot.is_active.is_(True)))
    ).all()
    created = 0
    for slot in slots:
        created += await generate_lessons_for_slot(db, slot)
    await db.commit()
    if created:
        logger.info("Сгенерировано уроков из расписания: %d", created)
    return created


async def deactivate_slot(db: AsyncSession, slot: ScheduleSlot) -> None:
    """Выключает слот и убирает его будущие нетронутые уроки.

    Удаляются только planned-уроки будущего: проведённые (история и деньги)
    и отменённые остаются.
    """
    slot.is_active = False
    future_planned = (
        await db.scalars(
            select(Lesson).where(
                Lesson.slot_id == slot.id,
                Lesson.status == LessonStatus.planned,
                Lesson.scheduled_at > datetime.now(ZoneInfo(get_settings().tz)),
            )
        )
    ).all()
    for lesson in future_planned:
        await db.delete(lesson)
    await db.commit()
