from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_own_parents
from app.models import Lesson, Parent, Student
from app.schemas.finance import BalanceOut, ChildBalance, ParentOverview
from app.schemas.lesson import LessonOut
from app.schemas.user import UserOut
from app.services.finance import student_balance

router = APIRouter(prefix="/parent", tags=["parent"])

ZERO = Decimal("0")


def _own_parent_for_student(parents: list[Parent], student_id: int) -> Parent:
    """Карточка родителя для конкретного ребёнка или 404 (чужой/несуществующий)."""
    for p in parents:
        if p.student_id == student_id:
            return p
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Ребёнок не найден")


@router.get("/children", response_model=ParentOverview)
async def children_overview(
    parents: list[Parent] = Depends(get_own_parents),
    db: AsyncSession = Depends(get_db),
):
    """Обзор: баланс/долг по каждому ребёнку + суммарный долг."""
    children: list[ChildBalance] = []
    total = ZERO
    for parent in parents:
        student = await db.get(Student, parent.student_id)
        bal = await student_balance(db, parent.student_id)
        children.append(
            ChildBalance(
                student_id=parent.student_id,
                student_name=student.user.full_name,
                lesson_price=bal.lesson_price,
                charged=bal.charged,
                paid=bal.paid,
                debt=bal.debt,
            )
        )
        total += bal.debt
    children.sort(key=lambda c: c.student_name)
    return ParentOverview(children=children, total_debt=total)


@router.get("/child/{student_id}")
async def child_card(
    student_id: int,
    parents: list[Parent] = Depends(get_own_parents),
    db: AsyncSession = Depends(get_db),
):
    """Карточка ребёнка только для чтения: расписание, цена, рекомендации."""
    parent = _own_parent_for_student(parents, student_id)
    student = await db.get(Student, parent.student_id)
    lessons = (
        await db.scalars(
            select(Lesson)
            .where(Lesson.student_id == parent.student_id)
            .order_by(Lesson.scheduled_at.desc())
        )
    ).all()
    return {
        "student": UserOut.model_validate(student.user),
        "lesson_price": parent.lesson_price,
        "recommendations": parent.recommendations,
        "lessons": [LessonOut.model_validate(lesson) for lesson in lessons],
    }


@router.get("/balance/{student_id}", response_model=BalanceOut)
async def balance(
    student_id: int,
    parents: list[Parent] = Depends(get_own_parents),
    db: AsyncSession = Depends(get_db),
):
    parent = _own_parent_for_student(parents, student_id)
    return await student_balance(db, parent.student_id)
