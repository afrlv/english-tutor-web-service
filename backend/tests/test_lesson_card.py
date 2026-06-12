import io

from tests.conftest import login
from tests.test_lessons import create_lesson


async def test_teacher_lesson_detail_with_student_name(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid)

    resp = await client.get(f"/api/lessons/{lesson['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["student_name"] == "Тест student"
    assert body["attachments"] == []


async def test_lesson_materials_file_and_link(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid)

    pdf = io.BytesIO(b"%PDF-1.4 fake")
    resp = await client.post(
        f"/api/lessons/{lesson['id']}/attachments",
        files={"file": ("unit3.pdf", pdf, "application/pdf")},
    )
    assert resp.status_code == 201
    file_id = resp.json()["id"]

    resp = await client.post(
        f"/api/lessons/{lesson['id']}/attachments/link",
        json={"url": "https://youtu.be/abc", "name": "Видео"},
    )
    assert resp.status_code == 201

    detail = (await client.get(f"/api/lessons/{lesson['id']}")).json()
    assert len(detail["attachments"]) == 2

    assert (await client.delete(f"/api/lesson-attachments/{file_id}")).status_code == 204
    detail = (await client.get(f"/api/lessons/{lesson['id']}")).json()
    assert len(detail["attachments"]) == 1


async def test_student_lesson_card(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    lesson = await create_lesson(client, sid)
    await client.post(
        f"/api/lessons/{lesson['id']}/attachments/link",
        json={"url": "https://quizlet.com/x", "name": "Карточки"},
    )
    await client.post(
        f"/api/lessons/{lesson['id']}/homeworks", json={"description": "Упр. 1"}
    )

    await login(client, "student@test.ru")
    resp = await client.get(f"/api/me/lessons/{lesson['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["attachments"][0]["name"] == "Карточки"
    assert body["homeworks"][0]["description"] == "Упр. 1"

    # Ученик не может управлять материалами урока
    resp = await client.post(
        f"/api/lessons/{lesson['id']}/attachments/link", json={"url": "https://x.io"}
    )
    assert resp.status_code == 403


async def test_student_cannot_see_foreign_lesson(client, seed_users):
    await login(client, "teacher@test.ru")
    # Второй ученик с уроком
    resp = await client.post(
        "/api/students", json={"email": "other@test.ru", "full_name": "Другой"}
    )
    other_sid = resp.json()["id"]
    foreign = await create_lesson(client, other_sid)

    await login(client, "student@test.ru")
    assert (await client.get(f"/api/me/lessons/{foreign['id']}")).status_code == 404
