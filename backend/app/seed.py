"""Идемпотентный сид: создаёт суперюзера и учителя из env, если их ещё нет.

Запуск: python -m app.seed
"""

import asyncio
import logging

from sqlalchemy import select

from app.config import get_settings
from app.db import async_session
from app.models import Role, User
from app.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.seed")


async def seed() -> None:
    settings = get_settings()
    accounts = [
        (settings.superuser_email, settings.superuser_password, Role.superuser, "Администратор"),
        (settings.teacher_email, settings.teacher_password, Role.teacher, "Учитель"),
    ]
    async with async_session() as db:
        for email, password, role, full_name in accounts:
            existing = await db.scalar(select(User).where(User.email == email))
            if existing is not None:
                logger.info("Пользователь %s уже существует, пропускаю", email)
                continue
            db.add(
                User(
                    email=email,
                    login=email,
                    hashed_password=hash_password(password),
                    full_name=full_name,
                    role=role,
                )
            )
            logger.info("Создан пользователь %s (%s)", email, role.value)
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
