from decimal import Decimal

from tests.conftest import login
from tests.test_lessons import create_lesson


async def test_conduct_creates_charge_with_price_snapshot(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, student_id)

    resp = await client.post(f"/api/lessons/{lesson['id']}/conduct")
    assert resp.status_code == 200
    assert resp.json()["status"] == "conducted"

    txs = (await client.get(f"/api/students/{student_id}/transactions")).json()
    assert len(txs) == 1
    assert txs[0]["type"] == "charge"
    assert Decimal(txs[0]["amount"]) == Decimal("1500")
    assert txs[0]["lesson_id"] == lesson["id"]

    # Повторное проведение отклоняется — двойного начисления нет
    resp = await client.post(f"/api/lessons/{lesson['id']}/conduct")
    assert resp.status_code == 409
    txs = (await client.get(f"/api/students/{student_id}/transactions")).json()
    assert len(txs) == 1


async def test_revert_deletes_charge_keeps_payments(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, student_id)
    await client.post(f"/api/lessons/{lesson['id']}/conduct")
    await client.post(
        f"/api/students/{student_id}/payments",
        json={"amount": "1000", "comment": "Перевод"},
    )

    resp = await client.post(f"/api/lessons/{lesson['id']}/revert")
    assert resp.status_code == 200
    assert resp.json()["status"] == "planned"

    txs = (await client.get(f"/api/students/{student_id}/transactions")).json()
    # Начисление удалено, оплата осталась
    assert len(txs) == 1
    assert txs[0]["type"] == "payment"
    assert Decimal(txs[0]["amount"]) == Decimal("1000")


async def test_summary_and_parent_balance_math(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    for _ in range(3):
        lesson = await create_lesson(client, student_id)
        await client.post(f"/api/lessons/{lesson['id']}/conduct")
    await client.post(f"/api/students/{student_id}/payments", json={"amount": "1000"})

    summary = (await client.get("/api/finance/summary")).json()
    assert Decimal(summary["total_earned"]) == Decimal("4500")
    row = summary["students"][0]
    assert Decimal(row["earned"]) == Decimal("4500")
    assert Decimal(row["paid"]) == Decimal("1000")
    assert Decimal(row["debt"]) == Decimal("3500")
    assert Decimal(row["lesson_price"]) == Decimal("1500")

    # Родитель видит тот же долг
    await login(client, "parent@test.ru")
    balance = (await client.get("/api/parent/balance/" + str(student_id))).json()
    assert Decimal(balance["charged"]) == Decimal("4500")
    assert Decimal(balance["paid"]) == Decimal("1000")
    assert Decimal(balance["debt"]) == Decimal("3500")
    assert Decimal(balance["lesson_price"]) == Decimal("1500")
    assert len(balance["transactions"]) == 4


async def test_prepayment_gives_negative_debt(client, seed_users):
    """Абонемент: оплата вперёд уводит долг в минус, агрегаты корректны."""
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    # Абонемент на 8 уроков по 1500
    await client.post(
        f"/api/students/{student_id}/payments",
        json={"amount": "12000", "comment": "Абонемент 8 уроков"},
    )
    lesson = await create_lesson(client, student_id)
    await client.post(f"/api/lessons/{lesson['id']}/conduct")

    row = (await client.get("/api/finance/summary")).json()["students"][0]
    assert Decimal(row["debt"]) == Decimal("-10500")  # предоплачено 7 уроков

    await login(client, "parent@test.ru")
    balance = (await client.get("/api/parent/balance/" + str(student_id))).json()
    assert Decimal(balance["debt"]) == Decimal("-10500")
    assert Decimal(balance["lesson_price"]) == Decimal("1500")


async def test_conduct_without_parent_card_rejected(client, seed_users):
    await login(client, "teacher@test.ru")
    resp = await client.post(
        "/api/students", json={"email": "orphan@test.ru", "full_name": "Без Родителя"}
    )
    new_student_id = resp.json()["id"]
    lesson = await create_lesson(client, new_student_id)

    resp = await client.post(f"/api/lessons/{lesson['id']}/conduct")
    assert resp.status_code == 409


async def test_negative_payment_rejected(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    resp = await client.post(
        f"/api/students/{student_id}/payments", json={"amount": "-100"}
    )
    assert resp.status_code == 422


async def test_price_change_does_not_rewrite_history(client, seed_users):
    student_id = seed_users["student_id"]
    parent_id = seed_users["parent_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, student_id)
    await client.post(f"/api/lessons/{lesson['id']}/conduct")

    resp = await client.patch(f"/api/parents/{parent_id}", json={"lesson_price": "2000"})
    assert resp.status_code == 200

    txs = (await client.get(f"/api/students/{student_id}/transactions")).json()
    assert Decimal(txs[0]["amount"]) == Decimal("1500")

    lesson2 = await create_lesson(client, student_id)
    await client.post(f"/api/lessons/{lesson2['id']}/conduct")
    summary = (await client.get("/api/finance/summary")).json()
    assert Decimal(summary["total_earned"]) == Decimal("3500")
