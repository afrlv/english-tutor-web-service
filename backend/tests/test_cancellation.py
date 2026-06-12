from datetime import datetime, timedelta
from decimal import Decimal

from tests.conftest import login
from tests.test_lessons import create_lesson


async def get_transactions(client, student_id: int) -> list[dict]:
    return (await client.get(f"/api/students/{student_id}/transactions")).json()


async def test_cancel_by_teacher_free(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid)

    resp = await client.post(
        f"/api/lessons/{lesson['id']}/cancel",
        json={"kind": "teacher", "comment": "Заболел"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "cancelled"
    assert body["cancellation_kind"] == "teacher"
    assert body["cancellation_comment"] == "Заболел"
    assert await get_transactions(client, sid) == []


async def test_cancel_by_student_in_advance_free(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid)
    resp = await client.post(
        f"/api/lessons/{lesson['id']}/cancel", json={"kind": "student"}
    )
    assert resp.json()["cancellation_kind"] == "student"
    assert await get_transactions(client, sid) == []


async def test_late_cancel_charges_full_price(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid)

    resp = await client.post(
        f"/api/lessons/{lesson['id']}/cancel", json={"kind": "late"}
    )
    assert resp.status_code == 200
    txs = await get_transactions(client, sid)
    assert len(txs) == 1
    assert Decimal(txs[0]["amount"]) == Decimal("1500")  # цена из seed
    assert txs[0]["lesson_id"] == lesson["id"]
    assert txs[0]["comment"] == "Поздняя отмена / неявка"


async def test_late_cancel_with_custom_amount(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid)

    resp = await client.post(
        f"/api/lessons/{lesson['id']}/cancel",
        json={"kind": "late", "charge_amount": "750"},
    )
    assert resp.status_code == 200
    txs = await get_transactions(client, sid)
    assert Decimal(txs[0]["amount"]) == Decimal("750")


async def test_restore_removes_charge(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid)
    await client.post(f"/api/lessons/{lesson['id']}/cancel", json={"kind": "late"})

    resp = await client.post(f"/api/lessons/{lesson['id']}/restore")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "planned"
    assert body["cancellation_kind"] is None
    assert await get_transactions(client, sid) == []


async def test_cancel_state_machine(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid)

    # Отменить дважды нельзя
    await client.post(f"/api/lessons/{lesson['id']}/cancel", json={"kind": "teacher"})
    resp = await client.post(
        f"/api/lessons/{lesson['id']}/cancel", json={"kind": "teacher"}
    )
    assert resp.status_code == 409

    # Провести отменённый нельзя
    assert (await client.post(f"/api/lessons/{lesson['id']}/conduct")).status_code == 409

    # Восстановить непроведённый-неотменённый нельзя
    await client.post(f"/api/lessons/{lesson['id']}/restore")
    resp = await client.post(f"/api/lessons/{lesson['id']}/restore")
    assert resp.status_code == 409

    # Отменить проведённый нельзя
    await client.post(f"/api/lessons/{lesson['id']}/conduct")
    resp = await client.post(
        f"/api/lessons/{lesson['id']}/cancel", json={"kind": "teacher"}
    )
    assert resp.status_code == 409


async def test_reschedule_keeps_original_time(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid)
    original = lesson["scheduled_at"]

    moved1 = (
        datetime.fromisoformat(original) + timedelta(days=1)
    ).isoformat()
    resp = await client.patch(
        f"/api/lessons/{lesson['id']}", json={"scheduled_at": moved1}
    )
    assert resp.json()["rescheduled_from"] == original

    # Второй перенос сохраняет ПЕРВОначальное время
    moved2 = (
        datetime.fromisoformat(original) + timedelta(days=2)
    ).isoformat()
    resp = await client.patch(
        f"/api/lessons/{lesson['id']}", json={"scheduled_at": moved2}
    )
    assert resp.json()["rescheduled_from"] == original

    # Правка темы без смены времени не делает урок «перенесённым»
    lesson2 = await create_lesson(client, sid)
    resp = await client.patch(f"/api/lessons/{lesson2['id']}", json={"topic": "New"})
    assert resp.json()["rescheduled_from"] is None


async def test_status_not_patchable_directly(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid)
    resp = await client.patch(
        f"/api/lessons/{lesson['id']}", json={"status": "conducted"}
    )
    # Поле игнорируется — статус меняется только явными действиями
    assert resp.status_code == 200
    assert resp.json()["status"] == "planned"
