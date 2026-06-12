from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.services.digest import compose_digest_lines
from tests.conftest import TestSession, login
from tests.test_lessons import create_lesson
from tests.test_schedule import create_slot

TZ = ZoneInfo(get_settings().tz)

ZOOM = "https://zoom.us/j/my-permanent-room"


async def set_zoom(client, sid: int, link: str | None) -> dict:
    resp = await client.patch(
        f"/api/students/{sid}", json={"default_zoom_link": link}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_default_zoom_autofill_on_create(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    await set_zoom(client, sid, ZOOM)

    # Без своей ссылки — подставляется постоянная
    lesson = await create_lesson(client, sid, zoom_link=None)
    assert lesson["zoom_link"] == ZOOM

    # Своя ссылка не перетирается
    lesson = await create_lesson(client, sid, zoom_link="https://zoom.us/j/special")
    assert lesson["zoom_link"] == "https://zoom.us/j/special"


async def test_default_zoom_in_generated_lessons(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    await set_zoom(client, sid, ZOOM)
    await create_slot(client, sid)

    lessons = (await client.get(f"/api/students/{sid}/lessons")).json()
    assert all(lesson["zoom_link"] == ZOOM for lesson in lessons)


async def test_zoom_change_updates_future_planned(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    await set_zoom(client, sid, ZOOM)
    lesson = await create_lesson(client, sid, zoom_link=None)
    special = await create_lesson(client, sid, zoom_link="https://zoom.us/j/special")

    new_zoom = "https://zoom.us/j/new-room"
    await set_zoom(client, sid, new_zoom)

    lessons = {l["id"]: l for l in (await client.get(f"/api/students/{sid}/lessons")).json()}
    assert lessons[lesson["id"]]["zoom_link"] == new_zoom
    assert lessons[special["id"]]["zoom_link"] == "https://zoom.us/j/special"


async def test_birthday_in_digest(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    today = datetime.now(TZ).date()
    resp = await client.patch(
        f"/api/students/{sid}",
        json={"birthday": today.replace(year=2012).isoformat()},
    )
    assert resp.status_code == 200
    assert resp.json()["birthday"] == today.replace(year=2012).isoformat()

    async with TestSession() as db:
        lines = await compose_digest_lines(db)
    assert any("день рождения у Тест student" in line for line in lines)

    # Не сегодня — не упоминается
    await client.patch(
        f"/api/students/{sid}",
        json={"birthday": (today - timedelta(days=40)).replace(year=2012).isoformat()},
    )
    async with TestSession() as db:
        lines = await compose_digest_lines(db)
    assert not any("день рождения" in line for line in lines)
