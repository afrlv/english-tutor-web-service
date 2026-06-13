from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timezone

from sqlalchemy import func

from app.db import get_db
from app.deps import get_current_user, require_roles
from app.models import EmailLog, Role, Student, User
from app.schemas.email import EmailLogOut, EmailSettingsIn, EmailSettingsOut
from app.schemas.user import PasswordSet, UserCreate, UserOut, UserUpdate
from app.security import hash_password
from app.services.digest import send_daily_digest
from app.services.email_settings import get_email_config, get_or_create_row
from app.services.mailer import send_email
from app.services.users import create_user, ensure_email_free, ensure_login_free

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_roles(Role.superuser))],
)


@router.get("/users", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    users = (
        await db.scalars(
            select(User).where(User.deleted_at.is_(None)).order_by(User.id)
        )
    ).all()
    # Число учеников по учителям — одним запросом
    counts = dict(
        (
            await db.execute(
                select(Student.teacher_id, func.count())
                .join(User, User.id == Student.user_id)
                .where(User.deleted_at.is_(None))
                .group_by(Student.teacher_id)
            )
        ).all()
    )
    result = []
    for u in users:
        out = UserOut.model_validate(u)
        if u.role == Role.teacher:
            out.students_count = counts.get(u.id, 0)
        result.append(out)
    return result


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
    if user is None or user.deleted_at is not None:
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
        if not data.is_active and user.is_active:
            user.token_version += 1  # деактивация отзывает активные сессии
        user.is_active = data.is_active
    await db.commit()
    return user


@router.post("/users/{user_id}/password")
async def set_password(
    user_id: int, data: PasswordSet, db: AsyncSession = Depends(get_db)
):
    user = await _get_user(user_id, db)
    user.hashed_password = hash_password(data.password)
    user.token_version += 1  # сброс пароля админом отзывает прежние сессии
    await db.commit()
    return {"detail": "Пароль установлен"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Мягкое удаление учётки: скрывается и теряет доступ; данные в БД целы."""
    if user_id == current.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Нельзя удалить самого себя")
    user = await _get_user(user_id, db)
    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False
    user.token_version += 1  # отзываем активные сессии удаляемого
    await db.commit()


@router.post("/digest/send-now")
async def send_digest_now(db: AsyncSession = Depends(get_db)):
    await send_daily_digest(db)
    return {"detail": "Дайджест отправлен"}


# --- Настройки почты и журнал отправки ---


def _settings_out(cfg) -> EmailSettingsOut:
    return EmailSettingsOut(
        backend=cfg.backend,
        smtp_host=cfg.smtp_host,
        smtp_port=cfg.smtp_port,
        smtp_user=cfg.smtp_user,
        smtp_from=cfg.smtp_from,
        password_set=bool(cfg.smtp_password),
    )


@router.get("/email-settings", response_model=EmailSettingsOut)
async def get_email_settings(db: AsyncSession = Depends(get_db)):
    return _settings_out(await get_email_config(db))


@router.put("/email-settings", response_model=EmailSettingsOut)
async def update_email_settings(
    data: EmailSettingsIn, db: AsyncSession = Depends(get_db)
):
    row = await get_or_create_row(db)
    row.backend = data.backend
    row.smtp_host = data.smtp_host
    row.smtp_port = data.smtp_port
    row.smtp_user = data.smtp_user
    row.smtp_from = data.smtp_from
    if data.smtp_password:
        row.smtp_password = data.smtp_password
    await db.commit()
    return _settings_out(await get_email_config(db))


@router.post("/email-settings/test")
async def send_test_email(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Тестовое письмо на почту администратора; результат виден в журнале."""
    ok = await send_email(
        db,
        user.email,
        "Проверка отправки почты",
        "Это тестовое письмо из кабинета репетитора. Если вы его читаете — отправка настроена.",
    )
    await db.commit()
    return {"ok": ok}


@router.get("/email-log", response_model=list[EmailLogOut])
async def email_log(limit: int = 100, db: AsyncSession = Depends(get_db)):
    return (
        await db.scalars(
            select(EmailLog)
            .order_by(EmailLog.created_at.desc(), EmailLog.id.desc())
            .limit(min(limit, 500))
        )
    ).all()
