from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import get_settings

from tests.conftest import TestSession, login

TZ = ZoneInfo(get_settings().tz)


def tomorrow_slot() -> dict:
    """Слот на завтрашний день недели — первый урок гарантированно в будущем."""
    tomorrow = datetime.now(TZ) + timedelta(days=1)
    return {"weekday": tomorrow.weekday(), "start_time": "16:00"}


async def create_slot(client, student_id: int, **overrides) -> dict:
    data = {**tomorrow_slot(), **overrides}
    resp = await client.post(f"/api/students/{student_id}/schedule", json=data)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_slot_generates_lessons_for_horizon(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    slot = await create_slot(client, student_id)

    lessons = (await client.get(f"/api/students/{student_id}/lessons")).json()
    # generate_weeks=4: завтра + 3 следующие недели
    assert len(lessons) == 4
    for lesson in lessons:
        at = datetime.fromisoformat(lesson["scheduled_at"]).astimezone(TZ)
        assert at.weekday() == slot["weekday"]
        assert at.strftime("%H:%M") == "16:00"
        assert lesson["status"] == "planned"


async def test_generation_is_idempotent(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    await create_slot(client, student_id)

    from app.services.schedule import generate_all

    async with TestSession() as db:
        created = await generate_all(db)
    assert created == 0

    lessons = (await client.get(f"/api/students/{student_id}/lessons")).json()
    assert len(lessons) == 4


async def test_moved_lesson_not_regenerated(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    await create_slot(client, student_id)
    lessons = (await client.get(f"/api/students/{student_id}/lessons")).json()
    first = lessons[-1]

    # Переносим первый урок серии на час позже
    moved_at = (
        datetime.fromisoformat(first["scheduled_at"]) + timedelta(hours=1)
    ).isoformat()
    resp = await client.patch(f"/api/lessons/{first['id']}", json={"scheduled_at": moved_at})
    assert resp.status_code == 200

    from app.services.schedule import generate_all

    async with TestSession() as db:
        created = await generate_all(db)
    assert created == 0  # дата слота занята перенесённым уроком

    lessons = (await client.get(f"/api/students/{student_id}/lessons")).json()
    assert len(lessons) == 4


async def test_delete_slot_removes_future_planned_keeps_conducted(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    slot = await create_slot(client, student_id)
    lessons = (await client.get(f"/api/students/{student_id}/lessons")).json()
    nearest = lessons[-1]

    # Ближайший урок проводим (нужна цена — карточка родителя есть в seed)
    assert (await client.post(f"/api/lessons/{nearest['id']}/conduct")).status_code == 200

    resp = await client.delete(f"/api/schedule/{slot['id']}")
    assert resp.status_code == 204

    lessons = (await client.get(f"/api/students/{student_id}/lessons")).json()
    assert len(lessons) == 1
    assert lessons[0]["status"] == "conducted"

    # Слот пропал из списка, генерация больше ничего не создаёт
    slots = (await client.get(f"/api/students/{student_id}/schedule")).json()
    assert slots == []


async def test_duplicate_slot_rejected(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    await create_slot(client, student_id)
    resp = await client.post(
        f"/api/students/{student_id}/schedule", json=tomorrow_slot()
    )
    assert resp.status_code == 409


async def test_schedule_rbac(client, seed_users):
    student_id = seed_users["student_id"]
    await login(client, "student@test.ru")
    assert (await client.get(f"/api/students/{student_id}/schedule")).status_code == 403
    resp = await client.post(
        f"/api/students/{student_id}/schedule", json=tomorrow_slot()
    )
    assert resp.status_code == 403
