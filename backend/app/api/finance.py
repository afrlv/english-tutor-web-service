from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.students import get_student_or_404
from app.db import get_db
from app.deps import require_roles
from app.models import Role, Student, Transaction, User
from app.schemas.finance import FinanceSummary, PaymentCreate, TransactionOut
from app.services import finance

router = APIRouter(
    tags=["finance"],
    dependencies=[Depends(require_roles(Role.teacher, Role.superuser))],
)


@router.get("/finance/summary", response_model=FinanceSummary)
async def summary(db: AsyncSession = Depends(get_db)):
    return await finance.finance_summary(db)


@router.get("/students/{student_id}/transactions", response_model=list[TransactionOut])
async def list_transactions(
    student: Student = Depends(get_student_or_404),
    db: AsyncSession = Depends(get_db),
):
    return (
        await db.scalars(
            select(Transaction)
            .where(Transaction.student_id == student.id)
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        )
    ).all()


@router.post(
    "/students/{student_id}/payments",
    response_model=TransactionOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_payment(
    data: PaymentCreate,
    student: Student = Depends(get_student_or_404),
    user: User = Depends(require_roles(Role.teacher, Role.superuser)),
    db: AsyncSession = Depends(get_db),
):
    return await finance.add_payment(
        db, student_id=student.id, amount=data.amount, comment=data.comment, actor=user
    )
