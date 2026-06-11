from tests.conftest import PASSWORD, login


async def test_login_ok(client, seed_users):
    resp = await client.post(
        "/api/auth/login", json={"login": "teacher@test.ru", "password": PASSWORD}
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "teacher"
    assert "access_token" in resp.cookies


async def test_login_wrong_password(client, seed_users):
    resp = await client.post(
        "/api/auth/login", json={"login": "teacher@test.ru", "password": "wrong"}
    )
    assert resp.status_code == 401


async def test_me_requires_auth(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_me_after_login(client, seed_users):
    await login(client, "student@test.ru")
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "student@test.ru"


async def test_change_password(client, seed_users):
    await login(client, "student@test.ru")
    resp = await client.post(
        "/api/auth/change-password",
        json={"current_password": PASSWORD, "new_password": "new-password-1"},
    )
    assert resp.status_code == 200

    resp = await client.post(
        "/api/auth/login",
        json={"login": "student@test.ru", "password": "new-password-1"},
    )
    assert resp.status_code == 200


async def test_inactive_user_cannot_login(client, seed_users):
    await login(client, "superuser@test.ru")
    users = (await client.get("/api/admin/users")).json()
    student_id = next(u["id"] for u in users if u["email"] == "student@test.ru")
    resp = await client.patch(f"/api/admin/users/{student_id}", json={"is_active": False})
    assert resp.status_code == 200

    resp = await client.post(
        "/api/auth/login", json={"login": "student@test.ru", "password": PASSWORD}
    )
    assert resp.status_code == 401
