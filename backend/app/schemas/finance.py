from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models import TransactionType


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    type: TransactionType
    amount: Decimal
    lesson_id: int | None
    comment: str | None
    created_at: datetime


class PaymentCreate(BaseModel):
    amount: Decimal
    comment: str | None = None


class StudentFinance(BaseModel):
    student_id: int
    student_name: str
    earned: Decimal
    paid: Decimal
    debt: Decimal
    # Цена урока с карточки родителя (0 — карточки нет) для пересчёта предоплаты в уроки
    lesson_price: Decimal


class FinanceSummary(BaseModel):
    total_earned: Decimal
    students: list[StudentFinance]


class BalanceOut(BaseModel):
    lesson_price: Decimal
    charged: Decimal
    paid: Decimal
    debt: Decimal
    transactions: list[TransactionOut]
