import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.emails.sender import get_email_sender
from app.emails.templates import digest_email
from app.models import Lesson, LessonStatus, Role, Student, User

logger = logging.getLogger("app.digest")


async def compose_digest_lines(db: AsyncSession, now: datetime | None = None) -> list[str]:
    """Строки вида «14:00 — Иван Петров, тема: Present Simple» по урокам на сегодня."""
    tz = ZoneInfo(get_settings().tz)
    now = now.astimezone(tz) if now else datetime.now(tz)
    day_start = datetime.combine(now.date(), time.min, tzinfo=tz)
    day_end = day_start + timedelta(days=1)

    rows = (
        await db.execute(
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
    ).all()

    lines = []
    for lesson, student_name in rows:
        at = lesson.scheduled_at.astimezone(tz).strftime("%H:%M")
        line = f"{at} — {student_name}"
        if lesson.topic:
            line += f", тема: {lesson.topic}"
        lines.append(line)
    return lines


async def send_daily_digest(db: AsyncSession) -> None:
    teacher = await db.scalar(
        select(User).where(User.role == Role.teacher, User.is_active.is_(True))
    )
    if teacher is None:
        logger.warning("Дайджест не отправлен: нет активного учителя")
        return
    lines = await compose_digest_lines(db)
    subject, body = digest_email(lines)
    await get_email_sender().send(teacher.email, subject, body)
