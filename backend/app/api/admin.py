from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_roles
from app.models import Role, User
from app.schemas.user import PasswordSet, UserCreate, UserOut, UserUpdate
from app.security import hash_password
from app.services.digest import send_daily_digest
from app.services.users import create_user, ensure_email_free, ensure_login_free

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_roles(Role.superuser))],
)


@router.get("/users", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    return (await db.scalars(select(User).order_by(User.id))).all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await create_user(
        db,
        email=data.email,
        login=data.login,
        full_name=data.full_name,
        role=data.role,
        password=data.password,
    )
    await db.commit()
    return user


async def _get_user(user_id: int, db: AsyncSession) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    return user


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await _get_user(user_id, db)


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int, data: UserUpdate, db: AsyncSession = Depends(get_db)
):
    user = await _get_user(user_id, db)
    if data.email is not None and data.email != user.email:
        await ensure_email_free(db, data.email)
        user.email = data.email
    if data.login is not None and data.login != user.login:
        await ensure_login_free(db, data.login)
        user.login = data.login
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    await db.commit()
    return user


@router.post("/users/{user_id}/password")
async def set_password(
    user_id: int, data: PasswordSet, db: AsyncSession = Depends(get_db)
):
    user = await _get_user(user_id, db)
    user.hashed_password = hash_password(data.password)
    await db.commit()
    return {"detail": "Пароль установлен"}


@router.post("/digest/send-now")
async def send_digest_now(db: AsyncSession = Depends(get_db)):
    await send_daily_digest(db)
    return {"detail": "Дайджест отправлен"}
