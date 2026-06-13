import secrets
import string
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import get_settings

password_hash = PasswordHash.recommended()

AUTH_COOKIE = "access_token"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def generate_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_access_token(
    user_id: int, role: str, token_version: int, impersonated_by: int | None = None
) -> str:
    """impersonated_by — id суперюзера, который смотрит систему от имени user_id.

    token_version вшивается в токен; рассинхрон с users.token_version
    инвалидирует токен (смена пароля/деактивация отзывают все сессии).
    """
    settings = get_settings()
    payload: dict = {
        "sub": str(user_id),
        "role": role,
        "tv": token_version,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_ttl_hours),
    }
    if impersonated_by is not None:
        payload["imp_by"] = impersonated_by
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
