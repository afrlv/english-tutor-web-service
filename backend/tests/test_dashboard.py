from decimal import Decimal

from tests.conftest import login
from tests.test_lessons import create_lesson


async def test_dashboard_basic_metrics(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    # 3 проведённых урока по 1500
    for _ in range(3):
        lesson = await create_lesson(client, sid)
        await client.post(f"/api/lessons/{lesson['id']}/conduct")
    await client.post(f"/api/students/{sid}/payments", json={"amount": "1500"})

    stats = (await client.get("/api/dashboard/stats")).json()
    assert Decimal(stats["earned_total"]) == Decimal("4500")
    assert Decimal(stats["debt_total"]) == Decimal("3000")
    assert stats["students_total"] == 1
    assert stats["students_active"] == 1  # есть проведённый урок (создаётся «завтра» в пределах 30 дней)
    assert len(stats["monthly"]) == 6
    assert stats["top_debtors"][0]["student_id"] == sid
    assert Decimal(stats["top_debtors"][0]["debt"]) == Decimal("3000")


async def test_dashboard_scoped_per_teacher(client, seed_users):
    # Дашборд показывает только своих учеников: у учителя без учеников — нули
    await login(client, "superuser@test.ru")
    resp = await client.post(
        "/api/admin/users",
        json={
            "email": "t3@test.ru",
            "full_name": "Учитель Три",
            "role": "teacher",
            "password": "t3pass123",
        },
    )
    assert resp.status_code == 201

    await client.post(
        "/api/auth/login", json={"login": "t3@test.ru", "password": "t3pass123"}
    )
    stats = (await client.get("/api/dashboard/stats")).json()
    assert stats["students_total"] == 0
    assert Decimal(stats["earned_total"]) == Decimal("0")
    assert stats["top_debtors"] == []


async def test_dashboard_rbac(client, seed_users):
    for role in ["student", "parent"]:
        await login(client, f"{role}@test.ru")
        assert (await client.get("/api/dashboard/stats")).status_code == 403
    # Суперюзер вне режима просмотра — 400 (нет своих учеников)
    await login(client, "superuser@test.ru")
    assert (await client.get("/api/dashboard/stats")).status_code == 400


async def test_admin_users_students_count(client, seed_users):
    await login(client, "superuser@test.ru")
    users = (await client.get("/api/admin/users")).json()
    teacher = next(u for u in users if u["email"] == "teacher@test.ru")
    assert teacher["students_count"] == 1
    student = next(u for u in users if u["email"] == "student@test.ru")
    assert student["students_count"] is None  # счётчик только у учителей
