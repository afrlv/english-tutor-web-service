from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user, get_token_payload
from app.models import Role, User
from app.schemas.user import ImpersonateIn, LoginIn, MeOut, PasswordChange, UserOut
from app.security import AUTH_COOKIE, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        AUTH_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.secure_cookies,
        max_age=settings.jwt_ttl_hours * 3600,
    )


@router.post("/login", response_model=UserOut)
async def login(data: LoginIn, response: Response, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(
        select(User).where((User.login == data.login) | (User.email == data.login))
    )
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный логин или пароль")
    if not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Учётная запись отключена")
    _set_auth_cookie(
        response, create_access_token(user.id, user.role.value, user.token_version)
    )
    return user


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(AUTH_COOKIE)
    return {"detail": "Выход выполнен"}


@router.get("/me", response_model=MeOut)
async def me(
    payload: dict = Depends(get_token_payload),
    user: User = Depends(get_current_user),
):
    out = MeOut.model_validate(user)
    out.impersonating = "imp_by" in payload
    return out


# --- Просмотр от имени другого пользователя (только суперюзер) ---


@router.get("/impersonation/targets", response_model=list[UserOut])
async def impersonation_targets(
    payload: dict = Depends(get_token_payload),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список профилей для переключателя. Доступен суперюзеру и в режиме просмотра."""
    if user.role != Role.superuser and "imp_by" not in payload:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав")
    return (
        await db.scalars(
            select(User)
            .where(User.is_active.is_(True), User.role != Role.superuser)
            .order_by(User.role, User.full_name)
        )
    ).all()


@router.post("/impersonate", response_model=MeOut)
async def impersonate(
    data: ImpersonateIn,
    response: Response,
    payload: dict = Depends(get_token_payload),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != Role.superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав")
    if "imp_by" in payload:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Сначала вернитесь в свой профиль"
        )
    target = await db.get(User, data.user_id)
    if target is None or not target.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    if target.id == user.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Это ваш собственный профиль")
    _set_auth_cookie(
        response,
        create_access_token(
            target.id, target.role.value, target.token_version, impersonated_by=user.id
        ),
    )
    out = MeOut.model_validate(target)
    out.impersonating = True
    return out


@router.post("/impersonate/stop", response_model=MeOut)
async def stop_impersonation(
    response: Response,
    payload: dict = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
):
    imp_by = payload.get("imp_by")
    if imp_by is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Вы не в режиме просмотра")
    superuser = await db.get(User, int(imp_by))
    if superuser is None or not superuser.is_active or superuser.role != Role.superuser:
        response.delete_cookie(AUTH_COOKIE)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Учётная запись недоступна")
    _set_auth_cookie(
        response,
        create_access_token(
            superuser.id, superuser.role.value, superuser.token_version
        ),
    )
    return MeOut.model_validate(superuser)


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Текущий пароль неверен")
    user.hashed_password = hash_password(data.new_password)
    user.token_version += 1  # отзываем прежние сессии
    await db.commit()
    # Текущему клиенту выдаём свежий токен, чтобы его не разлогинило
    _set_auth_cookie(
        response, create_access_token(user.id, user.role.value, user.token_version)
    )
    return {"detail": "Пароль изменён"}
