# Кабинет репетитора английского языка

Веб-сервис для одного репетитора: расписание уроков, домашние задания,
учёт денег и личные кабинеты для четырёх ролей.

| Роль | Что умеет |
|---|---|
| **Учитель** | Календарь (неделя/месяц), повторяющееся расписание, карточка урока (материалы, ДЗ, проверка с оценкой 2–5), история занятий лентой, отмены/переносы с правилами оплаты, наборы карточек для запоминания (аналог Quizlet), карточки учеников и родителей, финансы (начисления/оплаты/долги/абонементы), приватные заметки, ежедневный email-дайджест |
| **Ученик** | Карточка урока (материалы, zoom, ДЗ с ответом и оценкой), своё расписание, изучение наборов карточек (листание и ввод ответа), пройденные темы, комментарии, аватарка |
| **Родитель** | Расписание ребёнка (read-only), стоимость урока, баланс/предоплата и история оплат, рекомендации учителя |
| **Суперюзер** | Администратор платформы: заводит учителей, управляет пользователями (роли, логины, пароли), настройка почты и журнал отправки, просмотр системы от имени любого профиля |

Мультиарендный (SaaS): каждый учитель — арендатор, видит и ведёт только своих
учеников; данные арендаторов изолированы на уровне каждого запроса. Учителей
заводит суперюзер.

## Стек

- **Backend**: FastAPI (async) + PostgreSQL, SQLAlchemy 2 / Alembic, APScheduler, JWT в httpOnly cookie
- **Frontend**: Vue 3 + TypeScript + PrimeVue (Aura), FullCalendar, Pinia
- **Инфраструктура**: Docker Compose (postgres + backend + frontend с hot reload)

## Быстрый старт

```bash
cp .env.example .env        # поправьте JWT_SECRET и пароли сид-учёток
docker compose up -d
```

- Frontend: http://localhost:5173
- API: http://localhost:8000 (OpenAPI: `/docs`)
- Сид-учётки создаются на старте: суперюзер и учитель (`SUPERUSER_*`, `TEACHER_*` из `.env`)
- Миграции применяются автоматически при старте backend

По умолчанию письма пишутся в лог backend (`docker compose logs backend | grep EMAIL`).
Реальная отправка включается в кабинете администратора (`/admin/email`): выбор SMTP,
данные ящика, тестовое письмо; там же журнал всех отправленных писем. Env `EMAIL_BACKEND`/
`SMTP_*` — лишь значения по умолчанию до первого сохранения настроек в БД.

## Команды разработки

```bash
docker compose exec backend pytest                                  # backend-тесты
docker compose exec backend alembic revision --autogenerate -m ""   # новая миграция
cd frontend && npm test            # vitest
cd frontend && npm run typecheck   # vue-tsc
```

После добавления npm-зависимостей: `docker compose restart frontend`
(у контейнера свой volume node_modules).

## Деплой (CI/CD)

GitHub Actions (`.github/workflows/ci-cd.yml`): на каждый push/PR гоняются
backend-тесты (pytest + postgres) и frontend (typecheck, vitest, build). При
push в `main`, если тесты зелёные, образы backend и frontend **собираются в CI
и пушатся в GHCR** (`ghcr.io/<owner>/<repo>-backend|-frontend`), затем
**self-hosted runner** на сервере только тянет их и поднимает стек — без сборки
на VPS (иначе слабый сервер падает по OOM при `npm build`/`uv sync`).

Прод-стек — `docker-compose.prod.yml`: собранный фронт за nginx (отдаёт статику,
проксирует `/api` на backend, SPA-fallback), backend без reload, postgres только
внутри сети. Порт наружу — 80 (nginx). Образы тянутся из GHCR
(`docker compose pull && up -d`), приватные пакеты требуют `docker login ghcr.io`
— на раннере логин делает сам workflow.

Разовая подготовка сервера (Docker уже установлен):

```bash
# 1. Положить прод-окружение по пути, который ждёт workflow
cd ~ && git clone https://github.com/afrlv/english-tutor-web-service.git
cd ~/english-tutor-web-service
cp .env.prod.example .env && nano .env          # заполнить секреты, DEV_MODE=false

# 2. Поставить self-hosted runner (токен — в репо: Settings → Actions → Runners → New)
mkdir ~/actions-runner && cd ~/actions-runner
curl -o r.tar.gz -L https://github.com/actions/runner/releases/latest/download/actions-runner-linux-x64.tar.gz
tar xzf r.tar.gz
./config.sh --url https://github.com/afrlv/english-tutor-web-service --token <RUNNER_TOKEN>
sudo ./svc.sh install && sudo ./svc.sh start    # runner как systemd-сервис

# 3. Пользователь runner'а должен иметь доступ к docker
sudo usermod -aG docker $USER                   # перелогиниться/перезапустить сервис
```

Дальше каждый push в `main` после зелёного CI сам пересобирает и поднимает стек.

## Как устроены деньги

Неизменяемый леджер `transactions`: отметка «урок проведён» создаёт начисление
по цене с карточки родителя (снапшот — смена цены не переписывает историю),
оплаты вносятся вручную. Долг и заработок всегда считаются агрегатами,
числом нигде не хранятся. Один урок не может быть начислен дважды.

## Часовой пояс

Расписание, слоты и дайджест считаются в `TZ` из `.env` (по умолчанию
Europe/Moscow). Если занятия идут в другом поясе — поменяйте `TZ`.

Архитектурные решения и их обоснования — в `CLAUDE.md`, план развития — в `ROADMAP.md`.
