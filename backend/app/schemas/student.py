from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas.user import UserOut


class StudentCreate(BaseModel):
    email: EmailStr
    full_name: str


class StudentUpdate(BaseModel):
    full_name: str | None = None
    default_zoom_link: str | None = None
    birthday: date | None = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: UserOut
    created_at: datetime


class StudentTeacherOut(StudentOut):
    """Вид для учителя: включает приватную заметку."""

    teacher_private_note: str | None
    default_zoom_link: str | None = None
    birthday: date | None = None


class AttachStudentIn(BaseModel):
    user_id: int


class AssignTeacherIn(BaseModel):
    teacher_id: int


class UnassignedStudentOut(BaseModel):
    """Пользователь-ученик без карточки Student (создан админом, не привязан к учителю)."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: str
    full_name: str
    created_at: datetime


class PrivateNoteIn(BaseModel):
    teacher_private_note: str | None


class ParentCreate(BaseModel):
    email: EmailStr
    full_name: str
    lesson_price: Decimal = Decimal("0")
    recommendations: str | None = None


class ParentUpdate(BaseModel):
    full_name: str | None = None
    lesson_price: Decimal | None = None
    recommendations: str | None = None


class ParentAttach(BaseModel):
    """Привязать существующего родителя (учётку) к ещё одному ученику."""

    parent_user_id: int
    lesson_price: Decimal = Decimal("0")
    recommendations: str | None = None


class TeacherParentOut(BaseModel):
    """Родитель ученика учителя — для выбора при привязке второго ребёнка."""

    user_id: int
    full_name: str
    email: str
    children_count: int


class ParentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    user: UserOut
    lesson_price: Decimal
    recommendations: str | None
    created_at: datetime
