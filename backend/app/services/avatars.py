import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.services.file_signatures import matches_signature

MAX_SIZE = 2 * 1024 * 1024  # 2 МБ
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def save_avatar(file: UploadFile) -> str:
    """Сохраняет аватарку на диск, возвращает относительный путь для users.avatar_path."""
    ext = ALLOWED_TYPES.get(file.content_type or "")
    if ext is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Допустимы только JPEG, PNG или WebP"
        )
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Файл больше 2 МБ"
        )
    if not matches_signature(file.content_type or "", content):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Содержимое файла не соответствует типу",
        )
    avatars_dir = Path(get_settings().media_dir) / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4()}{ext}"
    (avatars_dir / name).write_bytes(content)
    return f"avatars/{name}"
