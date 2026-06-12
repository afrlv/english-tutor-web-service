def credentials_email(full_name: str, login: str, password: str) -> tuple[str, str]:
    subject = "Доступ к кабинету ученика"
    body = (
        f"Здравствуйте, {full_name}!\n\n"
        f"Для вас создан личный кабинет.\n"
        f"Логин: {login}\n"
        f"Пароль: {password}\n\n"
        f"Пароль можно сменить в кабинете после входа."
    )
    return subject, body


def reminder_email(
    full_name: str, when: str, topic: str | None, zoom_link: str | None
) -> tuple[str, str]:
    subject = "Напоминание об уроке английского"
    body = f"Здравствуйте, {full_name}!\n\nНапоминаем: {when} у вас урок английского."
    if topic:
        body += f"\nТема: {topic}"
    if zoom_link:
        body += f"\nСсылка на занятие: {zoom_link}"
    return subject, body


def digest_email(lines: list[str]) -> tuple[str, str]:
    subject = "Уроки на сегодня"
    if not lines:
        return subject, "Сегодня уроков нет."
    return subject, "Уроки на сегодня:\n" + "\n".join(lines)
