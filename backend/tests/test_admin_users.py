from tests.conftest import PASSWORD, login


async def test_admin_edits_login_and_name(client, seed_users):
    await login(client, "superuser@test.ru")
    users = (await client.get("/api/admin/users")).json()
    student = next(u for u in users if u["email"] == "student@test.ru")
    assert student["login"] == "student@test.ru"  # бэкофилл: логин = почта

    resp = await client.patch(
        f"/api/admin/users/{student['id']}",
        json={"login": "ivan2026", "full_name": "Иван Иванов"},
    )
    assert resp.status_code == 200
    assert resp.json()["login"] == "ivan2026"
    assert resp.json()["full_name"] == "Иван Иванов"
    assert resp.json()["email"] == "student@test.ru"  # почта не тронута

    # Вход работает и по новому логину, и по почте
    for cred in ["ivan2026", "student@test.ru"]:
        resp = await client.post(
            "/api/auth/login", json={"login": cred, "password": PASSWORD}
        )
        assert resp.status_code == 200, cred

    # Чужой занятый логин взять нельзя
    await login(client, "superuser@test.ru")
    resp = await client.patch(
        f"/api/admin/users/{student['id']}", json={"login": "teacher@test.ru"}
    )
    assert resp.status_code == 409


async def test_admin_edits_email_with_uniqueness(client, seed_users):
    await login(client, "superuser@test.ru")
    users = (await client.get("/api/admin/users")).json()
    student = next(u for u in users if u["email"] == "student@test.ru")

    resp = await client.patch(
        f"/api/admin/users/{student['id']}", json={"email": "parent@test.ru"}
    )
    assert resp.status_code == 409

    resp = await client.patch(
        f"/api/admin/users/{student['id']}", json={"email": "ivan-new@test.ru"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "ivan-new@test.ru"


async def test_admin_creates_user_with_custom_login(client, seed_users):
    await login(client, "superuser@test.ru")
    resp = await client.post(
        "/api/admin/users",
        json={
            "email": "petya@test.ru",
            "login": "petya",
            "full_name": "Пётр",
            "role": "student",
            "password": "petya-pass-1",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["login"] == "petya"

    resp = await client.post(
        "/api/auth/login", json={"login": "petya", "password": "petya-pass-1"}
    )
    assert resp.status_code == 200
