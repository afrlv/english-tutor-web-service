def credentials_email(
    full_name: str, login: str, password: str, site_url: str = ""
) -> tuple[str, str]:
    subject = "Доступ к кабинету ученика"
    body = (
        f"Здравствуйте, {full_name}!\n\n"
        f"Для вас создан личный кабинет.\n"
        f"Логин: {login}\n"
        f"Пароль: {password}\n\n"
    )
    if site_url:
        body += f"Войти в кабинет: {site_url}\n\n"
    body += "Пароль можно сменить в кабинете после входа."
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


def debt_notice_email(
    parent_name: str, student_name: str, debt: str, lessons_unpaid: int
) -> tuple[str, str]:
    subject = "Оплата занятий английским"
    body = (
        f"Здравствуйте, {parent_name}!\n\n"
        f"По занятиям ({student_name}) накопилась задолженность: {debt} ₽"
        f" — примерно {lessons_unpaid} занятия(ий).\n"
        f"Пожалуйста, оплатите удобным способом. Детали — в вашем кабинете."
    )
    return subject, body


def monthly_statement_email(
    parent_name: str,
    student_name: str,
    month_title: str,
    conducted: int,
    charged: str,
    paid: str,
    balance_line: str,
) -> tuple[str, str]:
    subject = f"Занятия английским: итоги за {month_title}"
    body = (
        f"Здравствуйте, {parent_name}!\n\n"
        f"Итоги месяца ({student_name}):\n"
        f"Проведено занятий: {conducted}\n"
        f"Начислено: {charged} ₽\n"
        f"Оплачено: {paid} ₽\n"
        f"{balance_line}\n\n"
        f"Подробная история — в вашем кабинете."
    )
    return subject, body


def digest_email(lines: list[str]) -> tuple[str, str]:
    subject = "Уроки на сегодня"
    if not lines:
        return subject, "Сегодня уроков нет."
    return subject, "Уроки на сегодня:\n" + "\n".join(lines)
