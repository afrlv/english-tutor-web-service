from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.students import comment_out
from app.db import get_db
from app.deps import get_own_student
from app.models import Homework, Lesson, Student, StudentComment
from app.schemas.comment import CommentCreate, CommentOut
from app.schemas.lesson import HomeworkOut, HomeworkStudentIn, LessonOut
from app.schemas.user import UserOut
from app.services.avatars import save_avatar

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/cabinet")
async def cabinet(
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    lessons = (
        await db.scalars(
            select(Lesson)
            .where(Lesson.student_id == student.id)
            .order_by(Lesson.scheduled_at.desc())
        )
    ).all()
    return {
        "user": UserOut.model_validate(student.user),
        "lessons": [LessonOut.model_validate(lesson) for lesson in lessons],
    }


@router.post("/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile,
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    student.user.avatar_path = await save_avatar(file)
    await db.commit()
    return student.user


@router.get("/homeworks", response_model=list[HomeworkOut])
async def my_homeworks(
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    return (
        await db.scalars(
            select(Homework)
            .join(Lesson, Lesson.id == Homework.lesson_id)
            .where(Lesson.student_id == student.id)
            .order_by(Homework.created_at.desc())
        )
    ).all()


@router.patch("/homeworks/{homework_id}", response_model=HomeworkOut)
async def update_my_homework(
    homework_id: int,
    data: HomeworkStudentIn,
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    homework = await db.scalar(
        select(Homework)
        .join(Lesson, Lesson.id == Homework.lesson_id)
        .where(Homework.id == homework_id, Lesson.student_id == student.id)
    )
    if homework is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задание не найдено")
    updates = data.model_dump(exclude_unset=True)
    if "is_done" in updates:
        homework.is_done = updates["is_done"]
    if "student_answer" in updates:
        homework.student_answer = updates["student_answer"]
    await db.commit()
    return homework


@router.get("/comments", response_model=list[CommentOut])
async def my_comments(
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    comments = (
        await db.scalars(
            select(StudentComment)
            .where(StudentComment.student_id == student.id)
            .order_by(StudentComment.created_at)
        )
    ).all()
    return [comment_out(c) for c in comments]


@router.post("/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_my_comment(
    data: CommentCreate,
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    comment = StudentComment(
        student_id=student.id, author_user_id=student.user_id, body=data.body
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment_out(comment)
