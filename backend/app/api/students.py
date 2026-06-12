from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_roles
from app.models import (
    Lesson,
    LessonStatus,
    Parent,
    Role,
    Student,
    StudentComment,
    User,
)
from app.schemas.comment import CommentCreate, CommentOut
from app.schemas.student import (
    ParentCreate,
    ParentOut,
    ParentUpdate,
    PrivateNoteIn,
    StudentCreate,
    StudentTeacherOut,
    StudentUpdate,
)
from app.schemas.user import PasswordSet
from app.security import hash_password
from app.services.users import create_user_with_credentials_email

router = APIRouter(
    tags=["students"],
    dependencies=[Depends(require_roles(Role.teacher, Role.superuser))],
)


async def get_student_or_404(
    student_id: int, db: AsyncSession = Depends(get_db)
) -> Student:
    student = await db.get(Student, student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ученик не найден")
    return student


@router.get("/students", response_model=list[StudentTeacherOut])
async def list_students(db: AsyncSession = Depends(get_db)):
    return (await db.scalars(select(Student).order_by(Student.id))).all()


@router.post(
    "/students", response_model=StudentTeacherOut, status_code=status.HTTP_201_CREATED
)
async def create_student(data: StudentCreate, db: AsyncSession = Depends(get_db)):
    """Создаёт пользователя-ученика и карточку; логин/пароль уходят на почту."""
    user = await create_user_with_credentials_email(
        db, email=data.email, full_name=data.full_name, role=Role.student
    )
    student = Student(user_id=user.id)
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


@router.get("/students/{student_id}", response_model=StudentTeacherOut)
async def get_student(student: Student = Depends(get_student_or_404)):
    return student


@router.patch("/students/{student_id}", response_model=StudentTeacherOut)
async def update_student(
    data: StudentUpdate,
    student: Student = Depends(get_student_or_404),
    db: AsyncSession = Depends(get_db),
):
    updates = data.model_dump(exclude_unset=True)
    if "full_name" in updates and updates["full_name"] is not None:
        student.user.full_name = updates["full_name"]
    if "birthday" in updates:
        student.birthday = updates["birthday"]
    if "default_zoom_link" in updates:
        new_link = updates["default_zoom_link"] or None
        old_link = student.default_zoom_link
        student.default_zoom_link = new_link
        # Будущие запланированные уроки без своей ссылки получают новую
        if new_link != old_link:
            future = (
                await db.scalars(
                    select(Lesson).where(
                        Lesson.student_id == student.id,
                        Lesson.status == LessonStatus.planned,
                        Lesson.scheduled_at > func.now(),
                        (Lesson.zoom_link.is_(None)) | (Lesson.zoom_link == old_link),
                    )
                )
            ).all()
            for lesson in future:
                lesson.zoom_link = new_link
    await db.commit()
    return student


@router.post("/students/{student_id}/password")
async def reset_student_password(
    data: PasswordSet,
    student: Student = Depends(get_student_or_404),
    db: AsyncSession = Depends(get_db),
):
    student.user.hashed_password = hash_password(data.password)
    await db.commit()
    return {"detail": "Пароль изменён"}


@router.patch("/students/{student_id}/private-note", response_model=StudentTeacherOut)
async def update_private_note(
    data: PrivateNoteIn,
    student: Student = Depends(get_student_or_404),
    db: AsyncSession = Depends(get_db),
):
    student.teacher_private_note = data.teacher_private_note
    await db.commit()
    return student


# --- Родители ---


@router.get("/students/{student_id}/parents", response_model=list[ParentOut])
async def list_parents(
    student: Student = Depends(get_student_or_404),
    db: AsyncSession = Depends(get_db),
):
    return (
        await db.scalars(select(Parent).where(Parent.student_id == student.id))
    ).all()


@router.post(
    "/students/{student_id}/parents",
    response_model=ParentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_parent(
    data: ParentCreate,
    student: Student = Depends(get_student_or_404),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.scalar(select(Parent).where(Parent.student_id == student.id))
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "У ученика уже есть карточка родителя"
        )
    user = await create_user_with_credentials_email(
        db, email=data.email, full_name=data.full_name, role=Role.parent
    )
    parent = Parent(
        user_id=user.id,
        student_id=student.id,
        lesson_price=data.lesson_price,
        recommendations=data.recommendations,
    )
    db.add(parent)
    await db.commit()
    await db.refresh(parent)
    return parent


@router.patch("/parents/{parent_id}", response_model=ParentOut)
async def update_parent(
    parent_id: int, data: ParentUpdate, db: AsyncSession = Depends(get_db)
):
    parent = await db.get(Parent, parent_id)
    if parent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Карточка родителя не найдена")
    if data.full_name is not None:
        parent.user.full_name = data.full_name
    if data.lesson_price is not None:
        parent.lesson_price = data.lesson_price
    if data.recommendations is not None:
        parent.recommendations = data.recommendations
    await db.commit()
    return parent


# --- Комментарии (сторона учителя) ---


def comment_out(c: StudentComment) -> CommentOut:
    return CommentOut(
        id=c.id,
        student_id=c.student_id,
        author_user_id=c.author_user_id,
        author_name=c.author.full_name,
        body=c.body,
        created_at=c.created_at,
    )


@router.get("/students/{student_id}/comments", response_model=list[CommentOut])
async def list_comments(
    student: Student = Depends(get_student_or_404),
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


@router.post(
    "/students/{student_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    data: CommentCreate,
    student: Student = Depends(get_student_or_404),
    user: User = Depends(require_roles(Role.teacher, Role.superuser)),
    db: AsyncSession = Depends(get_db),
):
    comment = StudentComment(
        student_id=student.id, author_user_id=user.id, body=data.body
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment_out(comment)
