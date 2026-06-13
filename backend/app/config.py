from functools import lru_cache

from pydantic_settings import BaseSettings

DEFAULT_JWT_SECRET = "dev-secret"


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://teacher:teacher@localhost:5432/teacher"

    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_ttl_hours: int = 24
    # В проде дефолтный секрет запрещён; в dev/тестах допускается
    dev_mode: bool = True
    # В проде (за HTTPS) включить — cookie только по защищённому соединению
    secure_cookies: bool = False

    superuser_email: str = "admin@example.com"
    superuser_password: str = "admin12345"
    teacher_email: str = "teacher@example.com"
    teacher_password: str = "teacher12345"

    email_backend: str = "console"  # console | smtp
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""  # по умолчанию — smtp_user

    # За сколько часов до урока напоминать ученику
    reminder_hours: int = 24

    scheduler_enabled: bool = False
    digest_hour: int = 7
    tz: str = "Europe/Moscow"
    # Горизонт материализации уроков из повторяющихся слотов
    generate_weeks: int = 4

    media_dir: str = "media"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.dev_mode and settings.jwt_secret == DEFAULT_JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET не задан: в проде (DEV_MODE=false) дефолтный секрет запрещён"
        )
    return settings
