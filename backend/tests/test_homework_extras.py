import io

from tests.conftest import login
from tests.test_lessons import create_lesson


async def create_homework(client, sid: int) -> dict:
    lesson = await create_lesson(client, sid)
    resp = await client.post(
        f"/api/lessons/{lesson['id']}/homeworks", json={"description": "Упр. 1"}
    )
    assert resp.status_code == 201
    return resp.json()


async def test_attachment_link_and_file(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    hw = await create_homework(client, sid)

    resp = await client.post(
        f"/api/homeworks/{hw['id']}/attachments/link",
        json={"url": "https://quizlet.com/set/1", "name": "Карточки"},
    )
    assert resp.status_code == 201
    assert resp.json()["url"] == "https://quizlet.com/set/1"

    pdf = io.BytesIO(b"%PDF-1.4 fake")
    resp = await client.post(
        f"/api/homeworks/{hw['id']}/attachments",
        files={"file": ("worksheet.pdf", pdf, "application/pdf")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "worksheet.pdf"
    assert body["file_path"].startswith("homework/")

    # Ученик видит оба вложения
    await login(client, "student@test.ru")
    homeworks = (await client.get("/api/me/homeworks")).json()
    assert len(homeworks[0]["attachments"]) == 2


async def test_attachment_bad_type_rejected(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    hw = await create_homework(client, sid)
    exe = io.BytesIO(b"MZ...")
    resp = await client.post(
        f"/api/homeworks/{hw['id']}/attachments",
        files={"file": ("virus.exe", exe, "application/octet-stream")},
    )
    assert resp.status_code == 422


async def test_attachment_signature_mismatch_rejected(client, seed_users):
    """Подделка content_type (exe под видом PDF) отсекается по сигнатуре."""
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    hw = await create_homework(client, sid)
    fake = io.BytesIO(b"MZ\x90\x00 not a pdf")
    resp = await client.post(
        f"/api/homeworks/{hw['id']}/attachments",
        files={"file": ("evil.pdf", fake, "application/pdf")},
    )
    assert resp.status_code == 422


async def test_student_answer_and_teacher_check(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    hw = await create_homework(client, sid)

    # Ученик пишет ответ и отмечает «сделано»
    await login(client, "student@test.ru")
    resp = await client.patch(
        f"/api/me/homeworks/{hw['id']}",
        json={"is_done": True, "student_answer": "I go to school every day."},
    )
    assert resp.status_code == 200
    assert resp.json()["student_answer"] == "I go to school every day."

    # Учитель видит ответ и отмечает «проверено»
    await login(client, "teacher@test.ru")
    resp = await client.patch(f"/api/homeworks/{hw['id']}", json={"is_checked": True})
    assert resp.json()["checked_at"] is not None

    # Снятие отметки
    resp = await client.patch(f"/api/homeworks/{hw['id']}", json={"is_checked": False})
    assert resp.json()["checked_at"] is None


async def test_grade_sets_checked(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    hw = await create_homework(client, sid)

    # Оценка автоматически отмечает работу проверенной
    resp = await client.patch(f"/api/homeworks/{hw['id']}", json={"grade": 5})
    body = resp.json()
    assert body["grade"] == 5
    assert body["checked_at"] is not None

    # Оценку можно изменить
    resp = await client.patch(f"/api/homeworks/{hw['id']}", json={"grade": 4})
    assert resp.json()["grade"] == 4

    # Снятие проверки очищает оценку
    resp = await client.patch(f"/api/homeworks/{hw['id']}", json={"is_checked": False})
    body = resp.json()
    assert body["checked_at"] is None
    assert body["grade"] is None


async def test_grade_bounds(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    hw = await create_homework(client, sid)
    for bad in [1, 6, 0]:
        resp = await client.patch(f"/api/homeworks/{hw['id']}", json={"grade": bad})
        assert resp.status_code == 422, bad


async def test_student_sees_grade_but_cannot_set(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    hw = await create_homework(client, sid)
    await client.patch(f"/api/homeworks/{hw['id']}", json={"grade": 5})

    await login(client, "student@test.ru")
    homeworks = (await client.get("/api/me/homeworks")).json()
    assert homeworks[0]["grade"] == 5

    # Поле grade в схеме ученика игнорируется
    resp = await client.patch(
        f"/api/me/homeworks/{hw['id']}", json={"grade": 2, "is_done": True}
    )
    assert resp.status_code == 200
    assert resp.json()["grade"] == 5


async def test_student_cannot_touch_attachments(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    hw = await create_homework(client, sid)
    resp = await client.post(
        f"/api/homeworks/{hw['id']}/attachments/link", json={"url": "https://x.io"}
    )
    attachment_id = resp.json()["id"]

    await login(client, "student@test.ru")
    resp = await client.post(
        f"/api/homeworks/{hw['id']}/attachments/link", json={"url": "https://evil.io"}
    )
    assert resp.status_code == 403
    assert (await client.delete(f"/api/attachments/{attachment_id}")).status_code == 403