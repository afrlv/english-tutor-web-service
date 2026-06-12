from datetime import datetime, timedelta

from zoneinfo import ZoneInfo

from app.config import get_settings

from app.services.digest import compose_digest_lines
from tests.conftest import TestSession, login
from tests.test_lessons import create_lesson

TZ = ZoneInfo(get_settings().tz)


async def test_digest_lists_today_lessons(client, seed_users):
    await login(client, "teacher@test.ru")
    today_at_14 = datetime.now(TZ).replace(hour=14, minute=0, second=0, microsecond=0)
    await create_lesson(
        client,
        seed_users["student_id"],
        scheduled_at=today_at_14.isoformat(),
        topic="Present Simple",
    )
    # Урок завтра в дайджест не попадает
    await create_lesson(
        client,
        seed_users["student_id"],
        scheduled_at=(today_at_14 + timedelta(days=1)).isoformat(),
    )

    async with TestSession() as db:
        lines = await compose_digest_lines(db, now=today_at_14)
    assert lines == ["14:00 — Тест student, тема: Present Simple"]


async def test_digest_empty_day(client, seed_users):
    async with TestSession() as db:
        lines = await compose_digest_lines(db)
    assert lines == []


async def test_send_now_emails_teacher(client, seed_users, fake_email):
    await login(client, "teacher@test.ru")
    today_at_10 = datetime.now(TZ).replace(hour=10, minute=0, second=0, microsecond=0)
    await create_lesson(
        client, seed_users["student_id"], scheduled_at=today_at_10.isoformat()
    )

    await login(client, "superuser@test.ru")
    resp = await client.post("/api/admin/digest/send-now")
    assert resp.status_code == 200

    assert len(fake_email.sent) == 1
    to, subject, body = fake_email.sent[0]
    assert to == "teacher@test.ru"
    assert subject == "Уроки на сегодня"
    assert "10:00 — Тест student" in body


async def test_send_now_empty(client, seed_users, fake_email):
    await login(client, "superuser@test.ru")
    resp = await client.post("/api/admin/digest/send-now")
    assert resp.status_code == 200
    assert fake_email.sent[0][2] == "Сегодня уроков нет."
