from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_own_parent
from app.models import Lesson, Parent, Student
from app.schemas.finance import BalanceOut
from app.schemas.lesson import LessonOut
from app.schemas.user import UserOut
from app.services.finance import student_balance

router = APIRouter(prefix="/parent", tags=["parent"])


@router.get("/child")
async def child_card(
    parent: Parent = Depends(get_own_parent),
    db: AsyncSession = Depends(get_db),
):
    """Карточка ребёнка только для чтения: расписание, цена, рекомендации.

    Приватная заметка учителя и комментарии сюда не попадают.
    """
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


@router.get("/balance", response_model=BalanceOut)
async def balance(
    parent: Parent = Depends(get_own_parent),
    db: AsyncSession = Depends(get_db),
):
    return await student_balance(db, parent.student_id)
