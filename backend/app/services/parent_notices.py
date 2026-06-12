import logging
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import lazyload

from app.config import get_settings
from app.emails.templates import debt_notice_email, monthly_statement_email
from app.models import (
    Lesson,
    LessonStatus,
    Parent,
    Student,
    Transaction,
    TransactionType,
    User,
)
from app.services.mailer import send_email

logger = logging.getLogger("app.parent_notices")

# Напоминаем о долге от 2 неоплаченных уроков, повторно — не чаще раза в неделю
DEBT_LESSONS_THRESHOLD = 2
NOTICE_COOLDOWN_DAYS = 7

MONTHS_RU = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]


async def _parent_rows(db: AsyncSession):
    """(parent, parent_user, student_user, charged, paid) по всем активным родителям."""
    charged = func.coalesce(
        func.sum(case((Transaction.type == TransactionType.charge, Transaction.amount), else_=0)), 0
    )
    paid = func.coalesce(
        func.sum(case((Transaction.type == TransactionType.payment, Transaction.amount), else_=0)), 0
    )
    StudentUser = User.__table__.alias("student_user")
    return (
        await db.execute(
            select(
                Parent,
                User,
                StudentUser.c.full_name.label("student_name"),
                charged.label("charged"),
                paid.label("paid"),
            )
            .join(User, User.id == Parent.user_id)
            .join(Student, Student.id == Parent.student_id)
            .join(StudentUser, StudentUser.c.id == Student.user_id)
            .outerjoin(Transaction, Transaction.student_id == Parent.student_id)
            .where(User.is_active.is_(True))
            .group_by(Parent.id, User.id, StudentUser.c.full_name)
            # Без eager-join Parent.user — он ломает GROUP BY
            .options(lazyload(Parent.user))
        )
    ).all()


def _fmt(amount: Decimal) -> str:
    return f"{amount:.0f}" if amount == amount.to_integral() else f"{amount:.2f}"


async def send_debt_notices(db: AsyncSession) -> int:
    """Напоминание о долге: от DEBT_LESSONS_THRESHOLD неоплаченных уроков.

    Повторное письмо — не раньше чем через NOTICE_COOLDOWN_DAYS; при погашении
    долга отметка сбрасывается, чтобы новый долг снова уведомил.
    """
    now = datetime.now(ZoneInfo(get_settings().tz))
    sent = 0
    for parent, parent_user, student_name, charged, paid in await _parent_rows(db):
        debt = charged - paid
        threshold = parent.lesson_price * DEBT_LESSONS_THRESHOLD
        if parent.lesson_price <= 0 or debt < threshold:
            if parent.debt_notice_sent_at is not None and debt <= 0:
                parent.debt_notice_sent_at = None
            continue
        if (
            parent.debt_notice_sent_at is not None
            and now - parent.debt_notice_sent_at < timedelta(days=NOTICE_COOLDOWN_DAYS)
        ):
            continue
        lessons_unpaid = int(debt // parent.lesson_price)
        subject, body = debt_notice_email(
            parent_user.full_name, student_name, _fmt(debt), lessons_unpaid
        )
        if await send_email(db, parent_user.email, subject, body):
            parent.debt_notice_sent_at = now
            sent += 1
    await db.commit()
    if sent:
        logger.info("Отправлено напоминаний о долге: %d", sent)
    return sent


async def send_monthly_statements(db: AsyncSession, now: datetime | None = None) -> int:
    """Выписка за прошедший месяц каждому родителю (1-го числа)."""
    tz = ZoneInfo(get_settings().tz)
    now = now.astimezone(tz) if now else datetime.now(tz)
    month_end = datetime.combine(now.date().replace(day=1), time.min, tzinfo=tz)
    month_start = (month_end - timedelta(days=1)).replace(day=1)
    month_title = f"{MONTHS_RU[month_start.month - 1]} {month_start.year}"

    sent = 0
    for parent, parent_user, student_name, charged_total, paid_total in await _parent_rows(db):
        conducted = (
            await db.scalar(
                select(func.count())
                .select_from(Lesson)
                .where(
                    Lesson.student_id == parent.student_id,
                    Lesson.status == LessonStatus.conducted,
                    Lesson.scheduled_at >= month_start,
                    Lesson.scheduled_at < month_end,
                )
            )
        ) or 0
        sums = (
            await db.execute(
                select(
                    func.coalesce(
                        func.sum(case((Transaction.type == TransactionType.charge, Transaction.amount), else_=0)), 0
                    ),
                    func.coalesce(
                        func.sum(case((Transaction.type == TransactionType.payment, Transaction.amount), else_=0)), 0
                    ),
                ).where(
                    Transaction.student_id == parent.student_id,
                    Transaction.created_at >= month_start,
                    Transaction.created_at < month_end,
                )
            )
        ).one()
        month_charged, month_paid = sums
        if conducted == 0 and month_charged == 0 and month_paid == 0:
            continue  # месяц без активности — не спамим

        debt = charged_total - paid_total
        if debt > 0:
            balance_line = f"Задолженность на сегодня: {_fmt(debt)} ₽"
        elif debt < 0:
            balance_line = f"Предоплачено на сегодня: {_fmt(-debt)} ₽"
        else:
            balance_line = "Баланс на сегодня: 0 ₽"

        subject, body = monthly_statement_email(
            parent_user.full_name,
            student_name,
            month_title,
            conducted,
            _fmt(month_charged),
            _fmt(month_paid),
            balance_line,
        )
        if await send_email(db, parent_user.email, subject, body):
            sent += 1
    await db.commit()
    if sent:
        logger.info("Отправлено месячных выписок: %d", sent)
    return sent
