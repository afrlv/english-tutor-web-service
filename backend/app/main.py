import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api import api_router
from app.config import get_settings

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    scheduler = None
    if settings.scheduler_enabled:
        from app.scheduler import create_scheduler

        scheduler = create_scheduler()
        scheduler.start()
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    app = FastAPI(title="Кабинет репетитора", lifespan=lifespan)
    app.include_router(api_router)

    # Каталог для загрузок; раздаётся не напрямую, а через /api/files с проверкой прав
    Path(get_settings().media_dir).mkdir(parents=True, exist_ok=True)
    return app


app = create_app()
