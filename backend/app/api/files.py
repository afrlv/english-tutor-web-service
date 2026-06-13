from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user
from app.models import (
    Homework,
    HomeworkAttachment,
    Lesson,
    LessonAttachment,
    Parent,
    Role,
    Student,
    User,
)

router = APIRouter(tags=["files"])


async def _student_access(user: User, student: Student | None, db: AsyncSession) -> bool:
    """Доступ к файлам ученика: суперюзер, его учитель, сам ученик, его родитель."""
    if student is None:
        return False
    if user.role == Role.superuser:
        return True
    if student.teacher_id == user.id:  # учитель-владелец
        return True
    if user.role == Role.student and student.user_id == user.id:
        return True
    if user.role == Role.parent:
        parent = await db.scalar(
            select(Parent).where(
                Parent.user_id == user.id, Parent.student_id == student.id
            )
        )
        return parent is not None
    return False


@router.get("/files/{path:path}")
async def get_file(
    path: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отдаёт файл только владельцу/учителю/родителю.

    Файл ищется в БД по точному пути — это и проверка прав, и защита от
    обхода каталога (на диск идём только за найденной записью).
    """
    allowed = False

    if path.startswith("avatars/"):
        owner = await db.scalar(select(User).where(User.avatar_path == path))
        if owner is not None:
            if user.role == Role.superuser or owner.id == user.id:
                allowed = True
            else:
                student = await db.scalar(select(Student).where(Student.user_id == owner.id))
                allowed = await _student_access(user, student, db)
    elif path.startswith("homework/"):
        # Файл может быть вложением ДЗ или материалом урока
        student_id = None
        hw_att = await db.scalar(
            select(HomeworkAttachment).where(HomeworkAttachment.file_path == path)
        )
        if hw_att is not None:
            hw = await db.get(Homework, hw_att.homework_id)
            lesson = await db.get(Lesson, hw.lesson_id)
            student_id = lesson.student_id
        else:
            les_att = await db.scalar(
                select(LessonAttachment).where(LessonAttachment.file_path == path)
            )
            if les_att is not None:
                lesson = await db.get(Lesson, les_att.lesson_id)
                student_id = lesson.student_id
        if student_id is not None:
            student = await db.get(Student, student_id)
            allowed = await _student_access(user, student, db)

    if not allowed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Файл не найден")

    full = Path(get_settings().media_dir) / path
    if not full.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Файл не найден")
    return FileResponse(full)
