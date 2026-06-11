from datetime import datetime, timedelta, timezone

from tests.conftest import login


async def create_lesson(client, student_id: int, **overrides) -> dict:
    data = {
        "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "topic": "Present Simple",
        "zoom_link": "https://zoom.us/j/123",
        "recommendation": "Повторить глаголы",
    }
    data.update(overrides)
    resp = await client.post(f"/api/students/{student_id}/lessons", json=data)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_lesson_crud_and_student_view(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, student_id)

    resp = await client.post(
        f"/api/lessons/{lesson['id']}/homeworks", json={"description": "Упр. 5 стр. 12"}
    )
    assert resp.status_code == 201
    homework = resp.json()

    # Ученик видит урок, zoom-ссылку и ДЗ в кабинете
    await login(client, "student@test.ru")
    cabinet = (await client.get("/api/me/cabinet")).json()
    assert len(cabinet["lessons"]) == 1
    assert cabinet["lessons"][0]["zoom_link"] == "https://zoom.us/j/123"
    assert cabinet["lessons"][0]["homeworks"][0]["description"] == "Упр. 5 стр. 12"

    # Ученик отмечает ДЗ сделанным
    resp = await client.patch(
        f"/api/me/homeworks/{homework['id']}", json={"is_done": True}
    )
    assert resp.status_code == 200
    assert resp.json()["is_done"] is True

    # Но не может трогать уроки учителя
    resp = await client.patch(f"/api/lessons/{lesson['id']}", json={"topic": "hack"})
    assert resp.status_code == 403


async def test_lesson_update_and_delete(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, student_id)

    resp = await client.patch(
        f"/api/lessons/{lesson['id']}", json={"topic": "Past Simple"}
    )
    assert resp.status_code == 200
    assert resp.json()["topic"] == "Past Simple"

    resp = await client.delete(f"/api/lessons/{lesson['id']}")
    assert resp.status_code == 204
    lessons = (await client.get(f"/api/students/{student_id}/lessons")).json()
    assert lessons == []


async def test_comments_flow(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    resp = await client.post(
        f"/api/students/{student_id}/comments", json={"body": "Молодец!"}
    )
    assert resp.status_code == 201

    await login(client, "student@test.ru")
    resp = await client.post("/api/me/comments", json={"body": "Спасибо"})
    assert resp.status_code == 201

    comments = (await client.get("/api/me/comments")).json()
    assert [c["body"] for c in comments] == ["Молодец!", "Спасибо"]


async def test_student_creation_sends_credentials(client, seed_users, fake_email):
    await login(client, "teacher@test.ru")
    resp = await client.post(
        "/api/students", json={"email": "new-student@test.ru", "full_name": "Новый Ученик"}
    )
    assert resp.status_code == 201

    assert len(fake_email.sent) == 1
    to, subject, body = fake_email.sent[0]
    assert to == "new-student@test.ru"
    assert "Логин: new-student@test.ru" in body
    assert "Пароль: " in body

    # Сгенерированный пароль из письма работает
    password = body.split("Пароль: ")[1].split("\n")[0].strip()
    resp = await client.post(
        "/api/auth/login", json={"login": "new-student@test.ru", "password": password}
    )
    assert resp.status_code == 200


async def test_duplicate_email_rejected(client, seed_users):
    await login(client, "teacher@test.ru")
    resp = await client.post(
        "/api/students", json={"email": "student@test.ru", "full_name": "Дубль"}
    )
    assert resp.status_code == 409


async def test_teacher_resets_student_password(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    resp = await client.post(
        f"/api/students/{student_id}/password", json={"password": "fresh-pass-1"}
    )
    assert resp.status_code == 200

    resp = await client.post(
        "/api/auth/login", json={"login": "student@test.ru", "password": "fresh-pass-1"}
    )
    assert resp.status_code == 200
