from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Lesson,
    LessonStatus,
    Parent,
    Student,
    Transaction,
    TransactionType,
    User,
)
from app.schemas.finance import BalanceOut, FinanceSummary, StudentFinance

ZERO = Decimal("0")

_charged = func.coalesce(
    func.sum(
        case((Transaction.type == TransactionType.charge, Transaction.amount), else_=0)
    ),
    0,
)
_paid = func.coalesce(
    func.sum(
        case((Transaction.type == TransactionType.payment, Transaction.amount), else_=0)
    ),
    0,
)


async def conduct_lesson(db: AsyncSession, lesson: Lesson, actor: User) -> None:
    """Урок проведён: статус + начисление по текущей цене с карточки родителя."""
    if lesson.status == LessonStatus.conducted:
        raise HTTPException(status.HTTP_409_CONFLICT, "Урок уже проведён")
    parent = await db.scalar(select(Parent).where(Parent.student_id == lesson.student_id))
    if parent is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Сначала заведите карточку родителя с ценой урока",
        )
    lesson.status = LessonStatus.conducted
    lesson.conducted_at = datetime.now(timezone.utc)
    db.add(
        Transaction(
            student_id=lesson.student_id,
            type=TransactionType.charge,
            amount=parent.lesson_price,
            lesson_id=lesson.id,
            created_by=actor.id,
        )
    )
    await db.commit()


async def revert_lesson(db: AsyncSession, lesson: Lesson) -> None:
    """Откат проведения: урок снова planned, связанное начисление удаляется."""
    if lesson.status != LessonStatus.conducted:
        raise HTTPException(status.HTTP_409_CONFLICT, "Урок не отмечен проведённым")
    charge = await db.scalar(
        select(Transaction).where(Transaction.lesson_id == lesson.id)
    )
    if charge is not None:
        await db.delete(charge)
    lesson.status = LessonStatus.planned
    lesson.conducted_at = None
    await db.commit()


async def add_payment(
    db: AsyncSession, *, student_id: int, amount: Decimal, comment: str | None, actor: User
) -> Transaction:
    if amount <= ZERO:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Сумма должна быть больше нуля")
    tx = Transaction(
        student_id=student_id,
        type=TransactionType.payment,
        amount=amount,
        comment=comment,
        created_by=actor.id,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx


async def finance_summary(db: AsyncSession) -> FinanceSummary:
    rows = (
        await db.execute(
            select(
                Student.id,
                User.full_name,
                _charged.label("earned"),
                _paid.label("paid"),
            )
            .join(User, User.id == Student.user_id)
            .outerjoin(Transaction, Transaction.student_id == Student.id)
            .group_by(Student.id, User.full_name)
            .order_by(User.full_name)
        )
    ).all()
    students = [
        StudentFinance(
            student_id=sid,
            student_name=name,
            earned=earned,
            paid=paid,
            debt=earned - paid,
        )
        for sid, name, earned, paid in rows
    ]
    return FinanceSummary(
        total_earned=sum((s.earned for s in students), ZERO), students=students
    )


async def student_balance(db: AsyncSession, student_id: int) -> BalanceOut:
    parent = await db.scalar(select(Parent).where(Parent.student_id == student_id))
    charged, paid = (
        await db.execute(
            select(_charged, _paid).where(Transaction.student_id == student_id)
        )
    ).one()
    transactions = (
        (
            await db.execute(
                select(Transaction)
                .where(Transaction.student_id == student_id)
                .order_by(Transaction.created_at.desc(), Transaction.id.desc())
            )
        )
        .scalars()
        .all()
    )
    return BalanceOut(
        lesson_price=parent.lesson_price if parent else ZERO,
        charged=charged,
        paid=paid,
        debt=charged - paid,
        transactions=transactions,
    )
