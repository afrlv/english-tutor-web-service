from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user, owns_student, require_roles
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
    AttachStudentIn,
    ParentCreate,
    ParentOut,
    ParentUpdate,
    PrivateNoteIn,
    StudentCreate,
    StudentTeacherOut,
    StudentUpdate,
    UnassignedStudentOut,
)
from app.schemas.user import PasswordSet
from app.security import hash_password
from app.services.users import create_user_with_credentials_email

router = APIRouter(
    tags=["students"],
    dependencies=[Depends(require_roles(Role.teacher, Role.superuser))],
)


async def get_student_or_404(
    student_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Student:
    student = await db.get(Student, student_id)
    # Чужой/удалённый ученик неотличим от несуществующего — единый 404
    if (
        student is None
        or not owns_student(user, student)
        or student.user.deleted_at is not None
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ученик не найден")
    return student


@router.get("/students", response_model=list[StudentTeacherOut])
async def list_students(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    query = (
        select(Student)
        .join(User, User.id == Student.user_id)
        .where(User.deleted_at.is_(None))
        .order_by(Student.id)
    )
    if user.role != Role.superuser:
        query = query.where(Student.teacher_id == user.id)
    return (await db.scalars(query)).all()


@router.post(
    "/students", response_model=StudentTeacherOut, status_code=status.HTTP_201_CREATED
)
async def create_student(
    data: StudentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создаёт пользователя-ученика и карточку; логин/пароль уходят на почту."""
    if user.role != Role.teacher:
        # Суперюзер заводит учеников от имени учителя (через режим просмотра)
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Создавать учеников может только учитель (войдите от имени учителя)",
        )
    # Если почту уже занял непривязанный ученик — подсказать привязать, а не плодить дубль
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing is not None:
        if (
            existing.role == Role.student
            and existing.deleted_at is None
            and await db.scalar(
                select(Student.id).where(Student.user_id == existing.id)
            )
            is None
        ):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Такой ученик уже заведён, но не привязан. "
                "Привяжите его через «Привязать существующего».",
            )
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Пользователь с такой почтой уже существует"
        )
    new_user = await create_user_with_credentials_email(
        db, email=data.email, full_name=data.full_name, role=Role.student
    )
    student = Student(user_id=new_user.id, teacher_id=user.id)
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


@router.get("/students-unassigned", response_model=list[UnassignedStudentOut])
async def list_unassigned_students(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Пользователи-ученики без карточки Student (созданы админом, ничьи).

    Пул общий: непривязанный ученик не принадлежит ни одному учителю, поэтому
    виден всем учителям и суперюзеру; забрать к себе может любой учитель.
    """
    rows = (
        await db.scalars(
            select(User)
            .outerjoin(Student, Student.user_id == User.id)
            .where(
                User.role == Role.student,
                User.deleted_at.is_(None),
                Student.id.is_(None),
            )
            .order_by(User.id)
        )
    ).all()
    return [
        UnassignedStudentOut(
            user_id=u.id, email=u.email, full_name=u.full_name, created_at=u.created_at
        )
        for u in rows
    ]


@router.post(
    "/students/attach",
    response_model=StudentTeacherOut,
    status_code=status.HTTP_201_CREATED,
)
async def attach_student(
    data: AttachStudentIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Учитель привязывает к себе непривязанного ученика (создаёт карточку Student)."""
    if user.role != Role.teacher:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Привязывать учеников может только учитель (войдите от имени учителя)",
        )
    target = await db.get(User, data.user_id)
    if target is None or target.role != Role.student or target.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ученик не найден")
    if await db.scalar(select(Student.id).where(Student.user_id == target.id)):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Этот ученик уже привязан к учителю"
        )
    student = Student(user_id=target.id, teacher_id=user.id)
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
    student.user.token_version += 1  # сброс пароля отзывает прежние сессии ученика
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
        await db.scalars(
            select(Parent)
            .join(User, User.id == Parent.user_id)
            .where(Parent.student_id == student.id, User.deleted_at.is_(None))
        )
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
    parent_id: int,
    data: ParentUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    parent = await db.get(Parent, parent_id)
    if parent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Карточка родителя не найдена")
    owner = await db.get(Student, parent.student_id)
    if owner is None or not owns_student(user, owner):
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
