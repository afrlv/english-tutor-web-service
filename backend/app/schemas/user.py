from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models import Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    login: str
    full_name: str
    role: Role
    avatar_path: str | None
    is_active: bool
    created_at: datetime
    # Только в списке /admin/users для учителей: число их учеников
    students_count: int | None = None


class UserCreate(BaseModel):
    email: EmailStr
    login: str | None = None  # по умолчанию — почта
    full_name: str
    role: Role
    password: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    login: str | None = None
    full_name: str | None = None
    role: Role | None = None
    is_active: bool | None = None


class PasswordSet(BaseModel):
    password: str


class MeOut(UserOut):
    """Ответ /auth/me: + флаг, что суперюзер смотрит систему от чужого имени."""

    impersonating: bool = False


class ImpersonateIn(BaseModel):
    user_id: int


class LoginIn(BaseModel):
    login: str  # логин или почта
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
