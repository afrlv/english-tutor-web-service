import jwt as pyjwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Parent, Role, Student, User
from app.security import AUTH_COOKIE, decode_access_token


async def get_token_payload(
    access_token: str | None = Cookie(default=None, alias=AUTH_COOKIE),
) -> dict:
    if not access_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Не выполнен вход")
    try:
        return decode_access_token(access_token)
    except pyjwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Недействительный токен")


async def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Учётная запись недоступна")
    return user


def require_roles(*roles: Role):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав")
        return user

    return dependency


async def get_own_student(
    user: User = Depends(require_roles(Role.student)),
    db: AsyncSession = Depends(get_db),
) -> Student:
    student = await db.scalar(select(Student).where(Student.user_id == user.id))
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Карточка ученика не найдена")
    return student


async def get_own_parent(
    user: User = Depends(require_roles(Role.parent)),
    db: AsyncSession = Depends(get_db),
) -> Parent:
    parent = await db.scalar(select(Parent).where(Parent.user_id == user.id))
    if parent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Карточка родителя не найдена")
    return parent
