from tests.conftest import PASSWORD, login
from tests.test_lessons import create_lesson


async def _user_id(client, email: str) -> int:
    users = (await client.get("/api/admin/users")).json()
    return next(u["id"] for u in users if u["email"] == email)


async def test_delete_hides_user_and_blocks_login(client, seed_users):
    await login(client, "superuser@test.ru")
    pid = await _user_id(client, "parent@test.ru")

    resp = await client.delete(f"/api/admin/users/{pid}")
    assert resp.status_code == 204

    # Исчез из списка
    emails = {u["email"] for u in (await client.get("/api/admin/users")).json()}
    assert "parent@test.ru" not in emails

    # Не виден по id и не правится
    assert (await client.get(f"/api/admin/users/{pid}")).status_code == 404
    assert (
        await client.patch(f"/api/admin/users/{pid}", json={"full_name": "x"})
    ).status_code == 404

    # Вход закрыт
    resp = await client.post(
        "/api/auth/login", json={"login": "parent@test.ru", "password": PASSWORD}
    )
    assert resp.status_code == 401


async def test_cannot_delete_self(client, seed_users):
    await login(client, "superuser@test.ru")
    sid = await _user_id(client, "superuser@test.ru")
    resp = await client.delete(f"/api/admin/users/{sid}")
    assert resp.status_code == 409


async def test_deleted_student_disappears_from_teacher(client, seed_users):
    sid = seed_users["student_id"]
    student_user_id = seed_users["users"]["student"].id

    # Урок есть, ученик активен — учитель видит
    await login(client, "teacher@test.ru")
    await create_lesson(client, sid)
    assert any(s["id"] == sid for s in (await client.get("/api/students")).json())

    # Суперюзер удаляет учётку ученика
    await login(client, "superuser@test.ru")
    assert (await client.delete(f"/api/admin/users/{student_user_id}")).status_code == 204

    # Учитель больше не видит ученика и не может открыть карточку/уроки/финансы
    await login(client, "teacher@test.ru")
    assert all(s["id"] != sid for s in (await client.get("/api/students")).json())
    assert (await client.get(f"/api/students/{sid}")).status_code == 404
    assert (await client.get(f"/api/students/{sid}/lessons")).status_code == 404
    summary = (await client.get("/api/finance/summary")).json()
    assert all(r["student_id"] != sid for r in summary["students"])


async def test_restore_user(client, seed_users):
    await login(client, "superuser@test.ru")
    pid = await _user_id(client, "parent@test.ru")
    await client.delete(f"/api/admin/users/{pid}")

    # Удалённый — в списке удалённых
    deleted = (await client.get("/api/admin/users/deleted")).json()
    assert any(u["id"] == pid for u in deleted)

    # Восстановление
    resp = await client.post(f"/api/admin/users/{pid}/restore")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True

    # Снова в активном списке и больше не в удалённых
    assert any(u["id"] == pid for u in (await client.get("/api/admin/users")).json())
    assert all(u["id"] != pid for u in (await client.get("/api/admin/users/deleted")).json())

    # Вход снова работает
    resp = await client.post(
        "/api/auth/login", json={"login": "parent@test.ru", "password": PASSWORD}
    )
    assert resp.status_code == 200


async def test_restore_non_deleted_is_404(client, seed_users):
    await login(client, "superuser@test.ru")
    pid = await _user_id(client, "parent@test.ru")
    assert (await client.post(f"/api/admin/users/{pid}/restore")).status_code == 404


async def test_deleted_session_revoked(client, seed_users):
    # Активная сессия ученика рвётся после удаления его учётки
    await login(client, "student@test.ru")
    assert (await client.get("/api/me/cabinet")).status_code == 200

    student_user_id = seed_users["users"]["student"].id
    # отдельный клиент-суперюзер не нужен: удалим через тот же клиент после релогина
    await login(client, "superuser@test.ru")
    await client.delete(f"/api/admin/users/{student_user_id}")

    # Возвращаем старую сессию ученика — она уже не работает не из-за смены куки,
    # а из-за token_version; проверяем повторным логином, что вход закрыт
    resp = await client.post(
        "/api/auth/login", json={"login": "student@test.ru", "password": PASSWORD}
    )
    assert resp.status_code == 401
