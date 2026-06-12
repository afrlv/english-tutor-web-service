from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.emails.smtp import SmtpEmailSender
from app.emails.sender import get_email_sender
from app.services.reminders import send_lesson_reminders
from tests.conftest import TestSession, login
from tests.test_lessons import create_lesson

TZ = ZoneInfo("Europe/Moscow")


async def run_reminders() -> int:
    async with TestSession() as db:
        return await send_lesson_reminders(db)


async def test_reminder_sent_once(client, seed_users, fake_email):
    await login(client, "teacher@test.ru")
    at = datetime.now(TZ) + timedelta(hours=3)
    await create_lesson(
        client,
        seed_users["student_id"],
        scheduled_at=at.isoformat(),
        topic="Present Simple",
    )

    assert await run_reminders() == 1
    to, subject, body = fake_email.sent[-1]
    assert to == "student@test.ru"
    assert subject == "Напоминание об уроке английского"
    assert "Тема: Present Simple" in body
    assert "https://zoom.us/j/123" in body

    # Повторный запуск ничего не шлёт
    assert await run_reminders() == 0


async def test_reminder_respects_window_and_status(client, seed_users, fake_email):
    await login(client, "teacher@test.ru")
    sid = seed_users["student_id"]
    now = datetime.now(TZ)

    # Далеко за горизонтом (reminder_hours=24)
    far = await create_lesson(client, sid, scheduled_at=(now + timedelta(hours=48)).isoformat())
    # В окне, но отменён
    cancelled = await create_lesson(client, sid, scheduled_at=(now + timedelta(hours=2)).isoformat())
    await client.patch(f"/api/lessons/{cancelled['id']}", json={"status": "cancelled"})

    assert await run_reminders() == 0
    assert far is not None  # просто фиксация, что урок создан


async def test_smtp_backend_selected(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "email_backend", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    sender = get_email_sender()
    assert isinstance(sender, SmtpEmailSender)


async def test_smtp_message_composition(monkeypatch):
    """Письмо собирается корректно; сетевую отправку подменяем."""
    captured = {}

    async def fake_send(msg, **kwargs):
        captured["msg"] = msg
        captured["kwargs"] = kwargs

    monkeypatch.setattr("app.emails.smtp.aiosmtplib.send", fake_send)
    settings = get_settings()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_user", "tutor@example.com")
    monkeypatch.setattr(settings, "smtp_password", "secret")

    await SmtpEmailSender(settings).send("to@example.com", "Тест", "Привет!")

    msg = captured["msg"]
    assert msg["To"] == "to@example.com"
    assert msg["From"] == "tutor@example.com"  # smtp_from пуст — берётся smtp_user
    assert msg["Subject"] == "Тест"
    assert captured["kwargs"]["hostname"] == "smtp.example.com"
    assert captured["kwargs"]["start_tls"] is True  # порт 587
