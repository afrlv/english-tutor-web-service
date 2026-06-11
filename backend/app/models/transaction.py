import enum
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin


class TransactionType(str, enum.Enum):
    charge = "charge"
    payment = "payment"


class Transaction(Base, CreatedAtMixin):
    """Неизменяемый леджер: charge — начисление за проведённый урок, payment — оплата.

    Долг = sum(charge) - sum(payment); заработок учителя = sum(charge).
    Никогда не хранится как число — только агрегаты.
    """

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type")
    )
    # Снапшот цены на момент урока: последующие изменения цены не переписывают историю
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # unique: один урок не может быть начислен дважды
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id"), unique=True)
    comment: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
