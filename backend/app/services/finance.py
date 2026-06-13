from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CancellationKind,
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


async def _get_parent_or_409(db: AsyncSession, student_id: int) -> Parent:
    parent = await db.scalar(select(Parent).where(Parent.student_id == student_id))
    if parent is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Сначала заведите карточку родителя с ценой урока",
        )
    return parent


async def conduct_lesson(db: AsyncSession, lesson: Lesson, actor: User) -> None:
    """Урок проведён: статус + начисление.

    Цена: lesson.price, если задана (0 — бесплатный пробный, начисления нет),
    иначе текущая цена с карточки родителя.
    """
    if lesson.status == LessonStatus.conducted:
        raise HTTPException(status.HTTP_409_CONFLICT, "Урок уже проведён")
    if lesson.status == LessonStatus.cancelled:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Урок отменён — сначала восстановите его"
        )
    if lesson.price is not None:
        amount = lesson.price
    else:
        parent = await _get_parent_or_409(db, lesson.student_id)
        amount = parent.lesson_price
    lesson.status = LessonStatus.conducted
    lesson.conducted_at = datetime.now(timezone.utc)
    if amount > ZERO:
        db.add(
            Transaction(
                student_id=lesson.student_id,
                type=TransactionType.charge,
                amount=amount,
                lesson_id=lesson.id,
                created_by=actor.id,
            )
        )
    await db.commit()


async def cancel_lesson(
    db: AsyncSession,
    lesson: Lesson,
    actor: User,
    *,
    kind: CancellationKind,
    comment: str | None = None,
    charge_amount: Decimal | None = None,
) -> None:
    """Отмена урока. Поздняя отмена/неявка — с начислением.

    Сумма начисления: charge_amount, если указана (например, 50% по правилам
    учителя), иначе полная цена с карточки родителя.
    """
    if lesson.status != LessonStatus.planned:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Отменить можно только запланированный урок"
        )
    if kind == CancellationKind.late:
        if charge_amount is not None:
            if charge_amount <= ZERO:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    "Сумма должна быть больше нуля",
                )
            amount = charge_amount
        elif lesson.price is not None:
            amount = lesson.price  # 0 у бесплатного пробного — начисления не будет
        else:
            parent = await _get_parent_or_409(db, lesson.student_id)
            amount = parent.lesson_price
        if amount > ZERO:
            db.add(
                Transaction(
                    student_id=lesson.student_id,
                    type=TransactionType.charge,
                    amount=amount,
                    lesson_id=lesson.id,
                    comment="Поздняя отмена / неявка",
                    created_by=actor.id,
                )
            )
    lesson.status = LessonStatus.cancelled
    lesson.cancellation_kind = kind
    lesson.cancellation_comment = comment
    await db.commit()


async def restore_lesson(db: AsyncSession, lesson: Lesson) -> None:
    """Восстановление отменённого урока: снова planned, начисление снимается."""
    if lesson.status != LessonStatus.cancelled:
        raise HTTPException(status.HTTP_409_CONFLICT, "Урок не отменён")
    charge = await db.scalar(
        select(Transaction).where(Transaction.lesson_id == lesson.id)
    )
    if charge is not None:
        await db.delete(charge)
    lesson.status = LessonStatus.planned
    lesson.cancellation_kind = None
    lesson.cancellation_comment = None
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


async def finance_summary(
    db: AsyncSession, teacher_id: int | None = None
) -> FinanceSummary:
    query = (
        select(
            Student.id,
            User.full_name,
            func.coalesce(func.max(Parent.lesson_price), 0).label("lesson_price"),
            _charged.label("earned"),
            _paid.label("paid"),
        )
        .join(User, User.id == Student.user_id)
        .outerjoin(Parent, Parent.student_id == Student.id)
        .outerjoin(Transaction, Transaction.student_id == Student.id)
        .group_by(Student.id, User.full_name)
        .order_by(User.full_name)
    )
    if teacher_id is not None:
        query = query.where(Student.teacher_id == teacher_id)
    rows = (await db.execute(query)).all()
    students = [
        StudentFinance(
            student_id=sid,
            student_name=name,
            lesson_price=price,
            earned=earned,
            paid=paid,
            debt=earned - paid,
        )
        for sid, name, price, earned, paid in rows
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
