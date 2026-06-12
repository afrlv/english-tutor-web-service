import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.emails.sender import get_email_sender
from app.emails.templates import reminder_email
from app.models import Lesson, LessonStatus, Student, User

logger = logging.getLogger("app.reminders")

WEEKDAYS_RU = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]


def _format_when(at: datetime, now: datetime) -> str:
    """«сегодня в 16:00», «завтра в 16:00» или «14.06 (суббота) в 16:00»."""
    if at.date() == now.date():
        day = "сегодня"
    elif at.date() == (now + timedelta(days=1)).date():
        day = "завтра"
    else:
        day = f"{at.strftime('%d.%m')} ({WEEKDAYS_RU[at.weekday()]})"
    return f"{day} в {at.strftime('%H:%M')}"


async def send_lesson_reminders(db: AsyncSession) -> int:
    """Шлёт ученикам напоминания о запланированных уроках в ближайшие reminder_hours.

    Урок помечается reminder_sent_at — повторно не напоминаем. Запускается
    каждые 15 минут; после простоя backend догоняет пропущенные напоминания
    (всё ещё актуальные уроки без отметки попадут в окно).
    """
    settings = get_settings()
    tz = ZoneInfo(settings.tz)
    now = datetime.now(tz)
    horizon = now + timedelta(hours=settings.reminder_hours)

    rows = (
        await db.execute(
            select(Lesson, User)
            .join(Student, Student.id == Lesson.student_id)
            .join(User, User.id == Student.user_id)
            .where(
                Lesson.status == LessonStatus.planned,
                Lesson.reminder_sent_at.is_(None),
                Lesson.scheduled_at > now,
                Lesson.scheduled_at <= horizon,
                User.is_active.is_(True),
            )
            .order_by(Lesson.scheduled_at)
        )
    ).all()

    sender = get_email_sender()
    sent = 0
    for lesson, student_user in rows:
        at_local = lesson.scheduled_at.astimezone(tz)
        subject, body = reminder_email(
            student_user.full_name,
            _format_when(at_local, now),
            lesson.topic,
            lesson.zoom_link,
        )
        await sender.send(student_user.email, subject, body)
        lesson.reminder_sent_at = now
        sent += 1
    await db.commit()
    if sent:
        logger.info("Отправлено напоминаний об уроках: %d", sent)
    return sent
