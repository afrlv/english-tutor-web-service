from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.emails.templates import credentials_email
from app.services.mailer import send_email
from app.models import Role, User
from app.security import generate_password, hash_password


async def ensure_email_free(db: AsyncSession, email: str) -> None:
    existing = await db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Пользователь с такой почтой уже существует"
        )


async def ensure_login_free(db: AsyncSession, login: str) -> None:
    existing = await db.scalar(select(User).where(User.login == login))
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Пользователь с таким логином уже существует"
        )


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    full_name: str,
    role: Role,
    password: str,
    login: str | None = None,
) -> User:
    login = login or email
    await ensure_email_free(db, email)
    await ensure_login_free(db, login)
    user = User(
        email=email,
        login=login,
        full_name=full_name,
        role=role,
        hashed_password=hash_password(password),
    )
    db.add(user)
    await db.flush()
    return user


async def create_user_with_credentials_email(
    db: AsyncSession, *, email: str, full_name: str, role: Role
) -> User:
    """Создаёт пользователя со сгенерированным паролем и шлёт логин/пароль на почту."""
    password = generate_password()
    user = await create_user(
        db, email=email, full_name=full_name, role=role, password=password
    )
    subject, body = credentials_email(
        full_name, user.login, password, get_settings().site_url
    )
    await send_email(db, email, subject, body)
    return user
