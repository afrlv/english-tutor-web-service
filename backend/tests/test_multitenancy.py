"""Изоляция арендаторов: учитель Б не видит и не трогает данные учителя А."""

import pytest_asyncio
from sqlalchemy import select

from app.models import Role, Student, User
from app.security import hash_password
from tests.conftest import PASSWORD, TestSession, login
from tests.test_lessons import create_lesson


@pytest_asyncio.fixture
async def second_teacher(seed_users):
    """Второй учитель со своим учеником — арендатор Б."""
    async with TestSession() as db:
        t2 = User(
            email="teacher2@test.ru",
            login="teacher2@test.ru",
            hashed_password=hash_password(PASSWORD),
            full_name="Учитель Два",
            role=Role.teacher,
        )
        db.add(t2)
        await db.flush()
        # ученик второго учителя
        su = User(
            email="student2@test.ru",
            login="student2@test.ru",
            hashed_password=hash_password(PASSWORD),
            full_name="Ученик Два",
            role=Role.student,
        )
        db.add(su)
        await db.flush()
        s2 = Student(user_id=su.id, teacher_id=t2.id)
        db.add(s2)
        await db.commit()
        return {"teacher_email": "teacher2@test.ru", "student_id": s2.id}


async def test_teacher_sees_only_own_students(client, seed_users, second_teacher):
    await login(client, "teacher@test.ru")
    own = (await client.get("/api/students")).json()
    ids = {s["id"] for s in own}
    assert seed_users["student_id"] in ids
    assert second_teacher["student_id"] not in ids


async def test_foreign_student_is_404(client, seed_users, second_teacher):
    foreign = second_teacher["student_id"]
    await login(client, "teacher@test.ru")
    assert (await client.get(f"/api/students/{foreign}")).status_code == 404
    assert (await client.get(f"/api/students/{foreign}/lessons")).status_code == 404
    assert (await client.get(f"/api/students/{foreign}/transactions")).status_code == 404
    assert (await client.get(f"/api/students/{foreign}/card-sets")).status_code == 404
    resp = await client.post(
        f"/api/students/{foreign}/payments", json={"amount": "100"}
    )
    assert resp.status_code == 404


async def test_foreign_lesson_and_objects_are_404(client, seed_users, second_teacher):
    # Учитель Б заводит урок своему ученику
    await login(client, "teacher2@test.ru")
    lesson = await create_lesson(client, second_teacher["student_id"])
    hw = (
        await client.post(
            f"/api/lessons/{lesson['id']}/homeworks", json={"description": "x"}
        )
    ).json()
    cs = (
        await client.post(
            f"/api/lessons/{lesson['id']}/card-sets", json={"title": "S", "cards": []}
        )
    ).json()

    # Учитель А не видит и не трогает чужой урок/ДЗ/набор
    await login(client, "teacher@test.ru")
    assert (await client.get(f"/api/lessons/{lesson['id']}")).status_code == 404
    assert (await client.post(f"/api/lessons/{lesson['id']}/conduct")).status_code == 404
    assert (
        await client.patch(f"/api/lessons/{lesson['id']}", json={"topic": "hack"})
    ).status_code == 404
    assert (await client.delete(f"/api/lessons/{lesson['id']}")).status_code == 404
    assert (
        await client.patch(f"/api/homeworks/{hw['id']}", json={"grade": 2})
    ).status_code == 404
    assert (await client.get(f"/api/card-sets/{cs['id']}")).status_code == 404
    assert (await client.delete(f"/api/card-sets/{cs['id']}")).status_code == 404


async def test_finance_summary_scoped(client, seed_users, second_teacher):
    # Каждый учитель видит в сводке только своих учеников
    await login(client, "teacher@test.ru")
    rows = (await client.get("/api/finance/summary")).json()["students"]
    ids = {r["student_id"] for r in rows}
    assert second_teacher["student_id"] not in ids

    await login(client, "teacher2@test.ru")
    rows = (await client.get("/api/finance/summary")).json()["students"]
    ids = {r["student_id"] for r in rows}
    assert ids == {second_teacher["student_id"]}


async def test_calendar_scoped(client, seed_users, second_teacher):
    await login(client, "teacher2@test.ru")
    await create_lesson(client, second_teacher["student_id"])
    mine = (await client.get("/api/lessons")).json()
    assert all(l["student_id"] == second_teacher["student_id"] for l in mine)

    await login(client, "teacher@test.ru")
    mine_a = (await client.get("/api/lessons")).json()
    assert all(l["student_id"] == seed_users["student_id"] for l in mine_a)


async def test_per_teacher_digest(client, seed_users, second_teacher, fake_email):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from app.config import get_settings
    from app.services.digest import send_daily_digest

    tz = ZoneInfo(get_settings().tz)
    at = datetime.now(tz).replace(hour=15, minute=0, second=0, microsecond=0)

    await login(client, "teacher@test.ru")
    await create_lesson(client, seed_users["student_id"], scheduled_at=at.isoformat(), topic="A-урок")
    await login(client, "teacher2@test.ru")
    await create_lesson(client, second_teacher["student_id"], scheduled_at=at.isoformat(), topic="Б-урок")

    fake_email.sent.clear()
    async with TestSession() as db:
        await send_daily_digest(db)

    by_to = {to: body for to, _subj, body in fake_email.sent}
    assert "A-урок" in by_to["teacher@test.ru"]
    assert "Б-урок" not in by_to["teacher@test.ru"]
    assert "Б-урок" in by_to["teacher2@test.ru"]
    assert "A-урок" not in by_to["teacher2@test.ru"]


async def test_token_version_revokes_session(client, seed_users):
    # Вход ученика, затем сброс пароля учителем — старая сессия инвалидна
    await login(client, "student@test.ru")
    assert (await client.get("/api/me/cabinet")).status_code == 200

    sid = seed_users["student_id"]
    # учитель сбрасывает пароль (через отдельный клиент-логин в той же сессии куки —
    # поэтому проверяем через прямой инкремент version в БД)
    async with TestSession() as db:
        student = await db.get(Student, sid)
        user = await db.get(User, student.user_id)
        user.token_version += 1
        await db.commit()

    # Прежняя кука теперь несёт устаревший tv → 401
    assert (await client.get("/api/me/cabinet")).status_code == 401
