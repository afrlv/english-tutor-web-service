"""Один родитель → несколько учеников: раздельные и суммарный долг."""

from decimal import Decimal

from tests.conftest import login
from tests.test_lessons import create_lesson


async def _conduct(client, student_id: int) -> None:
    lesson = await create_lesson(client, student_id)
    resp = await client.post(f"/api/lessons/{lesson['id']}/conduct")
    assert resp.status_code == 200, resp.text


async def test_parent_with_two_children(client, seed_users):
    sid1 = seed_users["student_id"]  # цена урока 1500 (seed)
    parent_user_id = seed_users["users"]["parent"].id

    await login(client, "teacher@test.ru")
    # Второй ученик того же учителя
    resp = await client.post(
        "/api/students", json={"email": "kid2@test.ru", "full_name": "Второй Ребёнок"}
    )
    assert resp.status_code == 201, resp.text
    sid2 = resp.json()["id"]

    # Родитель есть в списке родителей учителя (пока 1 ребёнок)
    parents = (await client.get("/api/teacher/parents")).json()
    assert any(
        p["user_id"] == parent_user_id and p["children_count"] == 1 for p in parents
    )

    # Привязать существующего родителя ко второму ученику со своей ценой
    resp = await client.post(
        f"/api/students/{sid2}/parents/attach",
        json={"parent_user_id": parent_user_id, "lesson_price": "1000"},
    )
    assert resp.status_code == 201, resp.text

    # Теперь у родителя 2 ребёнка
    parents = (await client.get("/api/teacher/parents")).json()
    assert any(
        p["user_id"] == parent_user_id and p["children_count"] == 2 for p in parents
    )

    # Провести уроки: ребёнок1 — 1 урок (1500), ребёнок2 — 2 урока (2×1000)
    await _conduct(client, sid1)
    await _conduct(client, sid2)
    await _conduct(client, sid2)

    # Родитель видит обоих детей с раздельным долгом и суммарным
    await login(client, "parent@test.ru")
    overview = (await client.get("/api/parent/children")).json()
    assert len(overview["children"]) == 2
    debts = {c["student_id"]: Decimal(c["debt"]) for c in overview["children"]}
    assert debts[sid1] == Decimal("1500")
    assert debts[sid2] == Decimal("2000")
    assert Decimal(overview["total_debt"]) == Decimal("3500")

    # Баланс конкретного ребёнка
    bal = (await client.get(f"/api/parent/balance/{sid2}")).json()
    assert Decimal(bal["debt"]) == Decimal("2000")
    assert Decimal(bal["lesson_price"]) == Decimal("1000")

    # Карточка ребёнка доступна
    assert (await client.get(f"/api/parent/child/{sid1}")).status_code == 200

    # Чужого ребёнка родитель не видит
    assert (await client.get("/api/parent/balance/999999")).status_code == 404
    assert (await client.get("/api/parent/child/999999")).status_code == 404


async def test_attach_rejects_foreign_parent(client, seed_users):
    """Нельзя привязать как родителя того, кто не родитель учеников этого учителя."""
    sid1 = seed_users["student_id"]
    superuser_id = seed_users["users"]["superuser"].id

    await login(client, "teacher@test.ru")
    resp = await client.post(
        "/api/students", json={"email": "kid3@test.ru", "full_name": "Третий"}
    )
    sid2 = resp.json()["id"]
    # superuser — не родитель → 404
    resp = await client.post(
        f"/api/students/{sid2}/parents/attach",
        json={"parent_user_id": superuser_id, "lesson_price": "500"},
    )
    assert resp.status_code == 404
    # к ученику с уже существующим родителем привязать нельзя → 409
    parent_user_id = seed_users["users"]["parent"].id
    resp = await client.post(
        f"/api/students/{sid1}/parents/attach",
        json={"parent_user_id": parent_user_id, "lesson_price": "500"},
    )
    assert resp.status_code == 409
