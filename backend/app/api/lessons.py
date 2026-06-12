from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.students import get_student_or_404
from app.db import get_db
from app.deps import require_roles
from app.models import Homework, Lesson, Role, ScheduleSlot, Student, User
from app.schemas.lesson import (
    HomeworkCreate,
    HomeworkOut,
    HomeworkUpdate,
    LessonCalendarOut,
    LessonCancelIn,
    LessonCreate,
    LessonOut,
    LessonUpdate,
)
from app.schemas.schedule import ScheduleSlotCreate, ScheduleSlotOut
from app.services import finance, schedule

router = APIRouter(
    tags=["lessons"],
    dependencies=[Depends(require_roles(Role.teacher, Role.superuser))],
)


async def get_lesson_or_404(lesson_id: int, db: AsyncSession = Depends(get_db)) -> Lesson:
    lesson = await db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Урок не найден")
    return lesson


@router.get("/lessons", response_model=list[LessonCalendarOut])
async def list_all_lessons(
    date_from: datetime | None = Query(None, alias="from"),
    date_to: datetime | None = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
):
    """Все уроки всех учеников (для календаря), опционально в диапазоне дат."""
    query = (
        select(Lesson, User.full_name)
        .join(Student, Student.id == Lesson.student_id)
        .join(User, User.id == Student.user_id)
        .order_by(Lesson.scheduled_at)
    )
    if date_from is not None:
        query = query.where(Lesson.scheduled_at >= date_from)
    if date_to is not None:
        query = query.where(Lesson.scheduled_at < date_to)
    rows = (await db.execute(query)).all()
    return [
        LessonCalendarOut(
            **LessonOut.model_validate(lesson).model_dump(), student_name=name
        )
        for lesson, name in rows
    ]


@router.get("/students/{student_id}/lessons", response_model=list[LessonOut])
async def list_lessons(
    student: Student = Depends(get_student_or_404),
    db: AsyncSession = Depends(get_db),
):
    return (
        await db.scalars(
            select(Lesson)
            .where(Lesson.student_id == student.id)
            .order_by(Lesson.scheduled_at.desc())
        )
    ).all()


@router.post(
    "/students/{student_id}/lessons",
    response_model=LessonOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_lesson(
    data: LessonCreate,
    student: Student = Depends(get_student_or_404),
    db: AsyncSession = Depends(get_db),
):
    lesson = Lesson(student_id=student.id, **data.model_dump())
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.patch("/lessons/{lesson_id}", response_model=LessonOut)
async def update_lesson(
    data: LessonUpdate,
    lesson: Lesson = Depends(get_lesson_or_404),
    db: AsyncSession = Depends(get_db),
):
    updates = data.model_dump(exclude_unset=True)
    # Перенос: запоминаем исходное время (только первое — «откуда перенесли»)
    if (
        "scheduled_at" in updates
        and updates["scheduled_at"] != lesson.scheduled_at
        and lesson.rescheduled_from is None
    ):
        lesson.rescheduled_from = lesson.scheduled_at
    for field, value in updates.items():
        setattr(lesson, field, value)
    await db.commit()
    return lesson


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson: Lesson = Depends(get_lesson_or_404),
    db: AsyncSession = Depends(get_db),
):
    await db.delete(lesson)
    await db.commit()


@router.post("/lessons/{lesson_id}/conduct", response_model=LessonOut)
async def conduct_lesson(
    lesson: Lesson = Depends(get_lesson_or_404),
    user: User = Depends(require_roles(Role.teacher, Role.superuser)),
    db: AsyncSession = Depends(get_db),
):
    await finance.conduct_lesson(db, lesson, user)
    return lesson


@router.post("/lessons/{lesson_id}/revert", response_model=LessonOut)
async def revert_lesson(
    lesson: Lesson = Depends(get_lesson_or_404),
    db: AsyncSession = Depends(get_db),
):
    await finance.revert_lesson(db, lesson)
    return lesson


@router.post("/lessons/{lesson_id}/cancel", response_model=LessonOut)
async def cancel_lesson(
    data: LessonCancelIn,
    lesson: Lesson = Depends(get_lesson_or_404),
    user: User = Depends(require_roles(Role.teacher, Role.superuser)),
    db: AsyncSession = Depends(get_db),
):
    await finance.cancel_lesson(
        db,
        lesson,
        user,
        kind=data.kind,
        comment=data.comment,
        charge_amount=data.charge_amount,
    )
    return lesson


@router.post("/lessons/{lesson_id}/restore", response_model=LessonOut)
async def restore_lesson(
    lesson: Lesson = Depends(get_lesson_or_404),
    db: AsyncSession = Depends(get_db),
):
    await finance.restore_lesson(db, lesson)
    return lesson


# --- Повторяющееся расписание ---


@router.get("/students/{student_id}/schedule", response_model=list[ScheduleSlotOut])
async def list_schedule(
    student: Student = Depends(get_student_or_404),
    db: AsyncSession = Depends(get_db),
):
    return (
        await db.scalars(
            select(ScheduleSlot)
            .where(ScheduleSlot.student_id == student.id, ScheduleSlot.is_active.is_(True))
            .order_by(ScheduleSlot.weekday, ScheduleSlot.start_time)
        )
    ).all()


@router.post(
    "/students/{student_id}/schedule",
    response_model=ScheduleSlotOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule_slot(
    data: ScheduleSlotCreate,
    student: Student = Depends(get_student_or_404),
    db: AsyncSession = Depends(get_db),
):
    duplicate = await db.scalar(
        select(ScheduleSlot).where(
            ScheduleSlot.student_id == student.id,
            ScheduleSlot.weekday == data.weekday,
            ScheduleSlot.start_time == data.start_time,
            ScheduleSlot.is_active.is_(True),
        )
    )
    if duplicate is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Такой слот уже есть")
    slot = ScheduleSlot(
        student_id=student.id, weekday=data.weekday, start_time=data.start_time
    )
    db.add(slot)
    await db.flush()
    await schedule.generate_lessons_for_slot(db, slot)
    await db.commit()
    await db.refresh(slot)
    return slot


@router.delete("/schedule/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule_slot(slot_id: int, db: AsyncSession = Depends(get_db)):
    slot = await db.get(ScheduleSlot, slot_id)
    if slot is None or not slot.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Слот не найден")
    await schedule.deactivate_slot(db, slot)


# --- Домашние задания ---


@router.post(
    "/lessons/{lesson_id}/homeworks",
    response_model=HomeworkOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_homework(
    data: HomeworkCreate,
    lesson: Lesson = Depends(get_lesson_or_404),
    db: AsyncSession = Depends(get_db),
):
    homework = Homework(lesson_id=lesson.id, description=data.description)
    db.add(homework)
    await db.commit()
    await db.refresh(homework)
    return homework


@router.patch("/homeworks/{homework_id}", response_model=HomeworkOut)
async def update_homework(
    homework_id: int, data: HomeworkUpdate, db: AsyncSession = Depends(get_db)
):
    homework = await db.get(Homework, homework_id)
    if homework is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задание не найдено")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(homework, field, value)
    await db.commit()
    return homework


@router.delete("/homeworks/{homework_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_homework(homework_id: int, db: AsyncSession = Depends(get_db)):
    homework = await db.get(Homework, homework_id)
    if homework is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задание не найдено")
    await db.delete(homework)
    await db.commit()
