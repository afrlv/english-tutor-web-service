from tests.conftest import login


async def test_settings_roundtrip_and_password_hidden(client, seed_users):
    await login(client, "superuser@test.ru")

    # До настройки — значения из env (console)
    resp = await client.get("/api/admin/email-settings")
    assert resp.status_code == 200
    assert resp.json()["backend"] == "console"
    assert resp.json()["password_set"] is False

    resp = await client.put(
        "/api/admin/email-settings",
        json={
            "backend": "smtp",
            "smtp_host": "smtp.example.com",
            "smtp_port": 465,
            "smtp_user": "tutor@example.com",
            "smtp_from": "Репетитор <tutor@example.com>",
            "smtp_password": "secret-app-password",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["backend"] == "smtp"
    assert body["smtp_host"] == "smtp.example.com"
    assert body["password_set"] is True
    assert "smtp_password" not in body  # пароль наружу не отдаём

    # Сохранение без пароля не сбрасывает его
    resp = await client.put(
        "/api/admin/email-settings",
        json={
            "backend": "smtp",
            "smtp_host": "smtp.example.com",
            "smtp_port": 465,
            "smtp_user": "tutor@example.com",
            "smtp_from": "",
            "smtp_password": None,
        },
    )
    assert resp.json()["password_set"] is True


async def test_test_email_and_log(client, seed_users, fake_email):
    await login(client, "superuser@test.ru")

    resp = await client.post("/api/admin/email-settings/test")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert fake_email.sent[-1][0] == "superuser@test.ru"

    log = (await client.get("/api/admin/email-log")).json()
    assert len(log) == 1
    assert log[0]["to_email"] == "superuser@test.ru"
    assert log[0]["status"] == "sent"
    assert log[0]["error"] is None


async def test_log_records_all_outgoing_mail(client, seed_users, fake_email):
    # Создание ученика учителем тоже попадает в журнал
    await login(client, "teacher@test.ru")
    await client.post(
        "/api/students", json={"email": "logged@test.ru", "full_name": "Журнал Тест"}
    )

    await login(client, "superuser@test.ru")
    log = (await client.get("/api/admin/email-log")).json()
    assert log[0]["to_email"] == "logged@test.ru"
    assert log[0]["subject"] == "Доступ к кабинету ученика"
    assert log[0]["status"] == "sent"


async def test_email_admin_rbac(client, seed_users):
    for role in ["teacher", "student", "parent"]:
        await login(client, f"{role}@test.ru")
        assert (await client.get("/api/admin/email-settings")).status_code == 403, role
        assert (await client.get("/api/admin/email-log")).status_code == 403, role
