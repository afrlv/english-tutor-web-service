from decimal import Decimal

from tests.conftest import login
from tests.test_lessons import create_lesson


async def get_transactions(client, sid: int) -> list[dict]:
    return (await client.get(f"/api/students/{sid}/transactions")).json()


async def test_lesson_defaults(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid)
    assert lesson["duration_minutes"] == 60
    assert lesson["price"] is None


async def test_custom_price_charged_on_conduct(client, seed_users):
    """Урок 90 минут по своей цене 2250 вместо 1500 с карточки."""
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(
        client, sid, duration_minutes=90, price="2250"
    )
    assert lesson["duration_minutes"] == 90

    await client.post(f"/api/lessons/{lesson['id']}/conduct")
    txs = await get_transactions(client, sid)
    assert Decimal(txs[0]["amount"]) == Decimal("2250")


async def test_free_trial_no_charge(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid, price="0")

    resp = await client.post(f"/api/lessons/{lesson['id']}/conduct")
    assert resp.status_code == 200
    assert resp.json()["status"] == "conducted"
    assert await get_transactions(client, sid) == []

    # Откат бесплатного урока тоже работает (нечего удалять — не падает)
    resp = await client.post(f"/api/lessons/{lesson['id']}/revert")
    assert resp.status_code == 200


async def test_free_trial_late_cancel_no_charge(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid, price="0")
    resp = await client.post(
        f"/api/lessons/{lesson['id']}/cancel", json={"kind": "late"}
    )
    assert resp.status_code == 200
    assert await get_transactions(client, sid) == []


async def test_late_cancel_uses_lesson_price(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid, price="2250")
    await client.post(f"/api/lessons/{lesson['id']}/cancel", json={"kind": "late"})
    txs = await get_transactions(client, sid)
    assert Decimal(txs[0]["amount"]) == Decimal("2250")


async def test_negative_price_rejected(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    resp = await client.post(
        f"/api/students/{sid}/lessons",
        json={"scheduled_at": "2026-07-01T12:00:00+05:00", "price": "-100"},
    )
    assert resp.status_code == 422
