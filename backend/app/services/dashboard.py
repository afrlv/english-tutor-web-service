from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import (
    Lesson,
    LessonStatus,
    Student,
    Transaction,
    TransactionType,
    User,
)
from app.schemas.dashboard import DashboardStats, DebtorRow, MonthEarning
from app.services.finance import finance_summary

ZERO = Decimal("0")


def _month_key(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def _last_6_months(now: datetime) -> list[str]:
    keys = []
    y, m = now.year, now.month
    for _ in range(6):
        keys.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(keys))


async def dashboard_stats(
    db: AsyncSession, teacher_id: int, now: datetime | None = None
) -> DashboardStats:
    tz = ZoneInfo(get_settings().tz)
    now = now.astimezone(tz) if now else datetime.now(tz)
    month_start = datetime(now.year, now.month, 1, tzinfo=tz)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = week_start + timedelta(days=7)
    cutoff_30 = now - timedelta(days=30)

    student_ids = (
        await db.scalars(
            select(Student.id)
            .join(User, User.id == Student.user_id)
            .where(Student.teacher_id == teacher_id, User.deleted_at.is_(None))
        )
    ).all()

    # Долги и общий заработок переиспользуем из finance_summary
    summary = await finance_summary(db, teacher_id=teacher_id)
    debt_total = sum((s.debt for s in summary.students), ZERO)
    top_debtors = [
        DebtorRow(student_id=s.student_id, student_name=s.student_name, debt=s.debt)
        for s in sorted(summary.students, key=lambda s: s.debt, reverse=True)
        if s.debt > ZERO
    ][:5]

    # Заработок по месяцам (charge-транзакции), агрегируем в TZ в Python
    earned_this_month = ZERO
    earned_prev_month = ZERO
    months = {k: ZERO for k in _last_6_months(now)}
    if student_ids:
        charges = (
            await db.execute(
                select(Transaction.amount, Transaction.created_at).where(
                    Transaction.student_id.in_(student_ids),
                    Transaction.type == TransactionType.charge,
                )
            )
        ).all()
        for amount, created_at in charges:
            local = created_at.astimezone(tz)
            key = _month_key(local)
            if key in months:
                months[key] += amount
            if local >= month_start:
                earned_this_month += amount
            elif local >= prev_month_start:
                earned_prev_month += amount

    monthly = [MonthEarning(month=k, earned=v) for k, v in months.items()]

    # Ученики: активные (проведённый урок за 30 дней) и затихшие (были, но молчат)
    students_total = len(student_ids)
    students_active = 0
    students_quiet = 0
    lessons_week_conducted = 0
    lessons_week_planned = 0
    lessons_month_conducted = 0
    if student_ids:
        active_ids = set(
            (
                await db.scalars(
                    select(Lesson.student_id)
                    .where(
                        Lesson.student_id.in_(student_ids),
                        Lesson.status == LessonStatus.conducted,
                        Lesson.scheduled_at >= cutoff_30,
                    )
                    .distinct()
                )
            ).all()
        )
        ever_conducted_ids = set(
            (
                await db.scalars(
                    select(Lesson.student_id)
                    .where(
                        Lesson.student_id.in_(student_ids),
                        Lesson.status == LessonStatus.conducted,
                    )
                    .distinct()
                )
            ).all()
        )
        students_active = len(active_ids)
        # Затихшие: занимались когда-то, но не за последние 30 дней
        students_quiet = len(ever_conducted_ids - active_ids)

        async def _count(*conds) -> int:
            return (
                await db.scalar(
                    select(func.count())
                    .select_from(Lesson)
                    .where(Lesson.student_id.in_(student_ids), *conds)
                )
            ) or 0

        lessons_week_conducted = await _count(
            Lesson.status == LessonStatus.conducted,
            Lesson.scheduled_at >= week_start,
            Lesson.scheduled_at < week_end,
        )
        lessons_week_planned = await _count(
            Lesson.status == LessonStatus.planned,
            Lesson.scheduled_at >= week_start,
            Lesson.scheduled_at < week_end,
        )
        lessons_month_conducted = await _count(
            Lesson.status == LessonStatus.conducted,
            Lesson.scheduled_at >= month_start,
        )

    return DashboardStats(
        earned_this_month=earned_this_month,
        earned_prev_month=earned_prev_month,
        earned_total=summary.total_earned,
        monthly=monthly,
        debt_total=debt_total,
        top_debtors=top_debtors,
        students_total=students_total,
        students_active=students_active,
        students_quiet=students_quiet,
        lessons_week_conducted=lessons_week_conducted,
        lessons_week_planned=lessons_week_planned,
        lessons_month_conducted=lessons_month_conducted,
    )
