from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.services.parent_notices import send_debt_notices, send_monthly_statements
from tests.conftest import TestSession, login
from tests.test_lessons import create_lesson

TZ = ZoneInfo(get_settings().tz)


async def conduct_n_lessons(client, sid: int, n: int) -> None:
    for _ in range(n):
        lesson = await create_lesson(client, sid)
        resp = await client.post(f"/api/lessons/{lesson['id']}/conduct")
        assert resp.status_code == 200


async def run_debt_notices() -> int:
    async with TestSession() as db:
        return await send_debt_notices(db)


async def test_debt_notice_threshold_and_cooldown(client, seed_users, fake_email):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")

    # 1 неоплаченный урок (порог 2) — тихо
    await conduct_n_lessons(client, sid, 1)
    assert await run_debt_notices() == 0

    # 2 неоплаченных — письмо родителю
    await conduct_n_lessons(client, sid, 1)
    assert await run_debt_notices() == 1
    to, subject, body = fake_email.sent[-1]
    assert to == "parent@test.ru"
    assert "задолженность: 3000" in body
    assert "2 занятия" in body

    # Кулдаун: повторный запуск молчит
    assert await run_debt_notices() == 0


async def test_debt_notice_resets_after_payment(client, seed_users, fake_email):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    await conduct_n_lessons(client, sid, 2)
    assert await run_debt_notices() == 1

    # Полная оплата сбрасывает отметку
    await client.post(f"/api/students/{sid}/payments", json={"amount": "3000"})
    assert await run_debt_notices() == 0

    # Новый долг до порога — снова письмо, без ожидания кулдауна
    await conduct_n_lessons(client, sid, 2)
    assert await run_debt_notices() == 1


async def test_monthly_statement_content(client, seed_users, fake_email):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")

    # Уроки и оплата «в прошлом месяце» относительно фиктивного «сейчас»
    now = datetime.now(TZ)
    await conduct_n_lessons(client, sid, 2)
    await client.post(
        f"/api/students/{sid}/payments", json={"amount": "1500", "comment": "Часть"}
    )

    fake_now = (now.replace(day=1) + timedelta(days=35)).replace(day=1)
    async with TestSession() as db:
        sent = await send_monthly_statements(db, now=fake_now)
    assert sent == 1
    to, subject, body = fake_email.sent[-1]
    assert to == "parent@test.ru"
    assert "Проведено занятий: 2" in body
    assert "Начислено: 3000" in body
    assert "Оплачено: 1500" in body
    assert "Задолженность на сегодня: 1500" in body


async def test_monthly_statement_skips_inactive_month(client, seed_users, fake_email):
    # Никакой активности — выписка не шлётся
    fake_now = datetime.now(TZ)
    async with TestSession() as db:
        sent = await send_monthly_statements(db, now=fake_now)
    assert sent == 0
    assert fake_email.sent == []
