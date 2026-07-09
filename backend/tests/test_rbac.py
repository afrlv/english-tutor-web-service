import pytest

from tests.conftest import login

# Матрица доступа: (метод, путь, роль → ожидаемый статус).
# 403 — роль не та; не-403 (200/404/422) — доступ по роли разрешён.
MATRIX = [
    ("GET", "/api/admin/users", {"superuser": 200, "teacher": 403, "student": 403, "parent": 403}),
    ("GET", "/api/students", {"superuser": 200, "teacher": 200, "student": 403, "parent": 403}),
    ("GET", "/api/finance/summary", {"superuser": 200, "teacher": 200, "student": 403, "parent": 403}),
    ("GET", "/api/me/cabinet", {"superuser": 403, "teacher": 403, "student": 200, "parent": 403}),
    ("GET", "/api/me/homeworks", {"student": 200, "teacher": 403}),
    ("GET", "/api/parent/children", {"superuser": 403, "teacher": 403, "student": 403, "parent": 200}),
]


@pytest.mark.parametrize("method,path,expectations", MATRIX)
async def test_rbac_matrix(client, seed_users, method, path, expectations):
    for role, expected in expectations.items():
        await login(client, f"{role}@test.ru")
        resp = await client.request(method, path)
        assert resp.status_code == expected, (
            f"{role} {method} {path}: ожидали {expected}, получили {resp.status_code}"
        )


async def test_unauthenticated_gets_401(client, seed_users):
    for path in ["/api/students", "/api/me/cabinet", "/api/parent/children", "/api/admin/users"]:
        resp = await client.get(path)
        assert resp.status_code == 401, path


async def test_private_note_hidden_from_student_and_parent(client, seed_users):
    """Личная заметка учителя не утекает в ответы ученика и родителя."""
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    resp = await client.patch(
        f"/api/students/{student_id}/private-note",
        json={"teacher_private_note": "СЕКРЕТНАЯ ЗАМЕТКА"},
    )
    assert resp.status_code == 200

    await login(client, "student@test.ru")
    for path in ["/api/me/cabinet", "/api/me/comments"]:
        body = (await client.get(path)).text
        assert "СЕКРЕТНАЯ ЗАМЕТКА" not in body, path

    await login(client, "parent@test.ru")
    for path in [f"/api/parent/child/{student_id}", f"/api/parent/balance/{student_id}"]:
        body = (await client.get(path)).text
        assert "СЕКРЕТНАЯ ЗАМЕТКА" not in body, path
