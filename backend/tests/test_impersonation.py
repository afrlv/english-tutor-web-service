from tests.conftest import login


async def test_superuser_impersonates_student(client, seed_users):
    student_user_id = seed_users["users"]["student"].id
    await login(client, "superuser@test.ru")

    resp = await client.post("/api/auth/impersonate", json={"user_id": student_user_id})
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "student"
    assert body["impersonating"] is True

    # Теперь работают эндпоинты ученика, а суперюзерские закрыты
    assert (await client.get("/api/me/cabinet")).status_code == 200
    assert (await client.get("/api/admin/users")).status_code == 403

    me = (await client.get("/api/auth/me")).json()
    assert me["email"] == "student@test.ru"
    assert me["impersonating"] is True


async def test_stop_impersonation_restores_superuser(client, seed_users):
    await login(client, "superuser@test.ru")
    await client.post(
        "/api/auth/impersonate", json={"user_id": seed_users["users"]["parent"].id}
    )
    assert (await client.get("/api/parent/children")).status_code == 200

    resp = await client.post("/api/auth/impersonate/stop")
    assert resp.status_code == 200
    assert resp.json()["role"] == "superuser"
    assert resp.json()["impersonating"] is False
    assert (await client.get("/api/admin/users")).status_code == 200


async def test_non_superuser_cannot_impersonate(client, seed_users):
    student_user_id = seed_users["users"]["student"].id
    for role in ["teacher", "student", "parent"]:
        await login(client, f"{role}@test.ru")
        resp = await client.post(
            "/api/auth/impersonate", json={"user_id": student_user_id}
        )
        assert resp.status_code == 403, role


async def test_impersonated_user_cannot_impersonate_further(client, seed_users):
    await login(client, "superuser@test.ru")
    await client.post(
        "/api/auth/impersonate", json={"user_id": seed_users["users"]["student"].id}
    )
    resp = await client.post(
        "/api/auth/impersonate", json={"user_id": seed_users["users"]["teacher"].id}
    )
    assert resp.status_code == 403


async def test_targets_available_while_impersonating(client, seed_users):
    await login(client, "superuser@test.ru")
    targets = (await client.get("/api/auth/impersonation/targets")).json()
    assert {t["role"] for t in targets} == {"teacher", "student", "parent"}

    await client.post(
        "/api/auth/impersonate", json={"user_id": seed_users["users"]["student"].id}
    )
    resp = await client.get("/api/auth/impersonation/targets")
    assert resp.status_code == 200

    # А обычному пользователю список недоступен
    await login(client, "teacher@test.ru")
    assert (await client.get("/api/auth/impersonation/targets")).status_code == 403


async def test_stop_without_impersonation_rejected(client, seed_users):
    await login(client, "superuser@test.ru")
    resp = await client.post("/api/auth/impersonate/stop")
    assert resp.status_code == 409
