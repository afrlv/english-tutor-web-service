import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.emails.templates import digest_email
from app.models import Lesson, LessonStatus, Role, Student, User
from app.services.mailer import send_email

logger = logging.getLogger("app.digest")


async def compose_digest_lines(
    db: AsyncSession, teacher_id: int | None = None, now: datetime | None = None
) -> list[str]:
    """Строки «14:00 — Иван Петров, тема: …» по урокам на сегодня.

    teacher_id ограничивает учениками конкретного учителя (None — все, для тестов).
    """
    tz = ZoneInfo(get_settings().tz)
    now = now.astimezone(tz) if now else datetime.now(tz)
    day_start = datetime.combine(now.date(), time.min, tzinfo=tz)
    day_end = day_start + timedelta(days=1)

    lessons_q = (
        select(Lesson, User.full_name)
        .join(Student, Student.id == Lesson.student_id)
        .join(User, User.id == Student.user_id)
        .where(
            Lesson.scheduled_at >= day_start,
            Lesson.scheduled_at < day_end,
            Lesson.status == LessonStatus.planned,
        )
        .order_by(Lesson.scheduled_at)
    )
    birthdays_q = (
        select(User.full_name)
        .join(Student, Student.user_id == User.id)
        .where(
            extract("month", Student.birthday) == now.month,
            extract("day", Student.birthday) == now.day,
            User.is_active.is_(True),
        )
    )
    if teacher_id is not None:
        lessons_q = lessons_q.where(Student.teacher_id == teacher_id)
        birthdays_q = birthdays_q.where(Student.teacher_id == teacher_id)

    rows = (await db.execute(lessons_q)).all()
    lines = []
    for lesson, student_name in rows:
        at = lesson.scheduled_at.astimezone(tz).strftime("%H:%M")
        line = f"{at} — {student_name}"
        if lesson.topic:
            line += f", тема: {lesson.topic}"
        lines.append(line)

    for name in (await db.scalars(birthdays_q)).all():
        lines.append(f"🎂 Сегодня день рождения у {name}!")
    return lines


async def send_daily_digest(db: AsyncSession) -> None:
    """Каждому активному учителю — свой дайджест по его ученикам."""
    teachers = (
        await db.scalars(
            select(User).where(User.role == Role.teacher, User.is_active.is_(True))
        )
    ).all()
    if not teachers:
        logger.warning("Дайджест не отправлен: нет активных учителей")
        return
    for teacher in teachers:
        lines = await compose_digest_lines(db, teacher_id=teacher.id)
        subject, body = digest_email(lines)
        await send_email(db, teacher.email, subject, body)
    await db.commit()
