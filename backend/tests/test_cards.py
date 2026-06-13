from tests.conftest import login


async def create_set(client, sid: int) -> dict:
    resp = await client.post(
        f"/api/students/{sid}/card-sets",
        json={
            "title": "Unit 3: Food",
            "cards": [
                {"front": "apple", "back": "яблоко"},
                {"front": "bread", "back": "хлеб"},
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_teacher_creates_set_with_cards(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    s = await create_set(client, sid)
    assert s["title"] == "Unit 3: Food"
    assert [c["front"] for c in s["cards"]] == ["apple", "bread"]

    # Добавление/правка/удаление карточек
    resp = await client.post(
        f"/api/card-sets/{s['id']}/cards", json={"front": "milk", "back": "молоко"}
    )
    assert resp.status_code == 201
    card_id = resp.json()["id"]
    resp = await client.patch(
        f"/api/cards/{card_id}", json={"front": "milk", "back": "молоко (напиток)"}
    )
    assert resp.json()["back"] == "молоко (напиток)"
    assert (await client.delete(f"/api/cards/{card_id}")).status_code == 204

    summaries = (await client.get(f"/api/students/{sid}/card-sets")).json()
    assert summaries[0]["total"] == 2
    assert summaries[0]["learned"] == 0


async def test_student_studies_and_progress_counts(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    s = await create_set(client, sid)
    apple_id = s["cards"][0]["id"]

    await login(client, "student@test.ru")
    my_sets = (await client.get("/api/me/card-sets")).json()
    assert my_sets[0]["total"] == 2

    full = (await client.get(f"/api/me/card-sets/{s['id']}")).json()
    assert len(full["cards"]) == 2

    # Два правильных ответа → карточка выучена (порог 2)
    await client.post(f"/api/me/cards/{apple_id}/answer", json={"correct": True})
    resp = await client.post(f"/api/me/cards/{apple_id}/answer", json={"correct": True})
    assert resp.json()["times_correct"] == 2

    my_sets = (await client.get("/api/me/card-sets")).json()
    assert my_sets[0]["learned"] == 1

    # Неправильный ответ считается отдельно
    resp = await client.post(f"/api/me/cards/{apple_id}/answer", json={"correct": False})
    assert resp.json()["times_wrong"] == 1


async def test_student_cannot_access_foreign_or_manage(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    s = await create_set(client, sid)

    await login(client, "student@test.ru")
    # Управление наборами ученику запрещено
    resp = await client.post(
        f"/api/students/{sid}/card-sets", json={"title": "x", "cards": []}
    )
    assert resp.status_code == 403
    assert (await client.delete(f"/api/card-sets/{s['id']}")).status_code == 403

    # Родителю карточки не видны
    await login(client, "parent@test.ru")
    assert (await client.get("/api/me/card-sets")).status_code == 403


async def test_lesson_card_sets(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    from tests.test_lessons import create_lesson

    lesson = await create_lesson(client, sid)
    resp = await client.post(
        f"/api/lessons/{lesson['id']}/card-sets",
        json={"title": "Слова урока", "cards": [{"front": "cat", "back": "кот"}]},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["lesson_id"] == lesson["id"]
    assert body["student_id"] == sid

    # Набор виден в списке урока
    lesson_sets = (await client.get(f"/api/lessons/{lesson['id']}/card-sets")).json()
    assert len(lesson_sets) == 1
    assert lesson_sets[0]["lesson_id"] == lesson["id"]

    # И в общем списке ученика (для повторения в кабинете)
    all_sets = (await client.get(f"/api/students/{sid}/card-sets")).json()
    assert len(all_sets) == 1

    # Ученик видит набор урока на его карточке
    await login(client, "student@test.ru")
    my = (await client.get(f"/api/me/lessons/{lesson['id']}/card-sets")).json()
    assert len(my) == 1
    assert my[0]["title"] == "Слова урока"


async def test_set_survives_lesson_delete(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    from tests.test_lessons import create_lesson

    lesson = await create_lesson(client, sid)
    await client.post(
        f"/api/lessons/{lesson['id']}/card-sets", json={"title": "Набор", "cards": []}
    )
    assert (await client.delete(f"/api/lessons/{lesson['id']}")).status_code == 204

    # Набор остаётся у ученика, но уже без привязки к уроку
    all_sets = (await client.get(f"/api/students/{sid}/card-sets")).json()
    assert len(all_sets) == 1
    assert all_sets[0]["lesson_id"] is None


async def test_delete_set_cascades(client, seed_users):
    sid = seed_users["student_id"]
    await login(client, "teacher@test.ru")
    s = await create_set(client, sid)
    assert (await client.delete(f"/api/card-sets/{s['id']}")).status_code == 204
    assert (await client.get(f"/api/students/{sid}/card-sets")).json() == []
