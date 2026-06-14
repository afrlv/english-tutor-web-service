from tests.conftest import login


async def _admin_create_student_user(client, email="orphan@test.ru"):
    """Админ заводит пользователя-ученика без карточки Student (непривязанный)."""
    await login(client, "superuser@test.ru")
    resp = await client.post(
        "/api/admin/users",
        json={
            "email": email,
            "full_name": "Сирота Тест",
            "role": "student",
            "password": "test-password-1",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_teacher_sees_and_attaches_unassigned(client, seed_users):
    user_id = await _admin_create_student_user(client)

    await login(client, "teacher@test.ru")
    # Непривязанный виден в пуле, но не в обычном списке учеников учителя
    unassigned = (await client.get("/api/students-unassigned")).json()
    assert any(u["user_id"] == user_id for u in unassigned)
    before = (await client.get("/api/students")).json()
    assert all(s["user"]["id"] != user_id for s in before)

    # Привязка к себе
    resp = await client.post("/api/students/attach", json={"user_id": user_id})
    assert resp.status_code == 201, resp.text
    assert resp.json()["user"]["id"] == user_id

    # Теперь он в списке учеников и ушёл из пула
    after = (await client.get("/api/students")).json()
    assert any(s["user"]["id"] == user_id for s in after)
    assert (await client.get("/api/students-unassigned")).json() == [] or all(
        u["user_id"] != user_id
        for u in (await client.get("/api/students-unassigned")).json()
    )


async def test_double_attach_conflicts(client, seed_users):
    user_id = await _admin_create_student_user(client)
    await login(client, "teacher@test.ru")
    assert (
        await client.post("/api/students/attach", json={"user_id": user_id})
    ).status_code == 201
    # Повторная привязка (или привязка уже чужого) — 409
    resp = await client.post("/api/students/attach", json={"user_id": user_id})
    assert resp.status_code == 409


async def test_create_student_with_unassigned_email_hints_attach(client, seed_users):
    await _admin_create_student_user(client, email="dup@test.ru")
    await login(client, "teacher@test.ru")
    resp = await client.post(
        "/api/students", json={"email": "dup@test.ru", "full_name": "Дубль"}
    )
    assert resp.status_code == 409
    assert "привяж" in resp.json()["detail"].lower()


async def test_admin_assigns_teacher(client, seed_users):
    user_id = await _admin_create_student_user(client)
    teacher_id = seed_users["users"]["teacher"].id

    await login(client, "superuser@test.ru")
    resp = await client.post(
        f"/api/admin/users/{user_id}/assign-teacher", json={"teacher_id": teacher_id}
    )
    assert resp.status_code == 201, resp.text

    # Ученик появился у учителя
    await login(client, "teacher@test.ru")
    students = (await client.get("/api/students")).json()
    assert any(s["user"]["id"] == user_id for s in students)


async def test_attach_rejects_non_student(client, seed_users):
    """Нельзя привязать как ученика того, кто не student."""
    teacher_id = seed_users["users"]["teacher"].id
    await login(client, "teacher@test.ru")
    resp = await client.post("/api/students/attach", json={"user_id": teacher_id})
    assert resp.status_code == 404
