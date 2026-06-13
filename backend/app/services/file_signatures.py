"""Проверка содержимого файла по сигнатуре (magic bytes).

Content-Type из запроса подделывается; проверяем реальные первые байты,
чтобы под видом картинки/PDF не загрузили произвольный файл.
"""


def _is_pdf(b: bytes) -> bool:
    return b[:4] == b"%PDF"


def _is_jpeg(b: bytes) -> bool:
    return b[:3] == b"\xff\xd8\xff"


def _is_png(b: bytes) -> bool:
    return b[:8] == b"\x89PNG\r\n\x1a\n"


def _is_webp(b: bytes) -> bool:
    return b[:4] == b"RIFF" and b[8:12] == b"WEBP"


def _is_mp3(b: bytes) -> bool:
    # ID3-тег или MPEG frame sync (0xFFEx/0xFFFx)
    return b[:3] == b"ID3" or (len(b) >= 2 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0)


def _is_mp4(b: bytes) -> bool:
    # ftyp-бокс на смещении 4 (m4a/mp4)
    return b[4:8] == b"ftyp"


def _is_ogg(b: bytes) -> bool:
    return b[:4] == b"OggS"


def _is_wav(b: bytes) -> bool:
    return b[:4] == b"RIFF" and b[8:12] == b"WAVE"


# content_type → список допустимых проверок (несколько форматов делят тип)
_CHECKS = {
    "application/pdf": [_is_pdf],
    "image/jpeg": [_is_jpeg],
    "image/png": [_is_png],
    "image/webp": [_is_webp],
    "audio/mpeg": [_is_mp3],
    "audio/mp4": [_is_mp4],
    "audio/x-m4a": [_is_mp4],
    "audio/ogg": [_is_ogg],
    "audio/wav": [_is_wav],
}


def matches_signature(content_type: str, content: bytes) -> bool:
    """True, если байты соответствуют заявленному content_type."""
    checks = _CHECKS.get(content_type)
    if not checks:
        return False
    return any(check(content) for check in checks)
