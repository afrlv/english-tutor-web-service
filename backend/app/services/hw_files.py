import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.services.file_signatures import matches_signature

MAX_SIZE = 10 * 1024 * 1024  # 10 МБ
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
}


async def save_homework_file(file: UploadFile) -> tuple[str, str]:
    """Сохраняет файл ДЗ, возвращает (относительный путь, исходное имя)."""
    ext = ALLOWED_TYPES.get(file.content_type or "")
    if ext is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Допустимы PDF, изображения и аудио (mp3, m4a, ogg, wav)",
        )
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Файл больше 10 МБ")
    if not matches_signature(file.content_type or "", content):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Содержимое файла не соответствует типу",
        )
    hw_dir = Path(get_settings().media_dir) / "homework"
    hw_dir.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid.uuid4()}{ext}"
    (hw_dir / stored).write_bytes(content)
    return f"homework/{stored}", file.filename or stored
