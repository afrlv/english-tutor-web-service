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
и пушатся в GHCR** (`ghcr.io/<owner>/<repo>-backend|-frontend`) — сборка на
GitHub-раннерах, чтобы не падать по OOM на слабом VPS при `npm build`/`uv sync`.

**Деплой — вручную** (сервер 0.5 ГБ RAM: self-hosted раннер отключён, чтобы не
конкурировать за память с приложением — на таком объёме раннер + стек не живут
вместе). После зелёного CI обновить сервер по SSH:

```bash
ssh afrlv@<server>
cd ~/english-tutor-web-service
git pull                                              # свежий compose/конфиг
docker compose -f docker-compose.prod.yml --env-file .env pull   # образы из GHCR
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

Прод-стек — `docker-compose.prod.yml`: собранный фронт за nginx (отдаёт статику,
проксирует `/api` на backend, SPA-fallback), backend без reload, postgres только
внутри сети. Порты наружу — 80 и 443 (nginx). Образы в GHCR публичные — `pull`
идёт без логина; если закрыть в private, перед pull нужен `docker login ghcr.io`.

### HTTPS (домен + Let's Encrypt)

Домен `repetitor-diary.ru` (A-записи `@`, `www`, `*` → IP сервера). TLS
терминирует nginx-фронт, серт выпускает/продлевает контейнер `certbot` (webroot
`/.well-known/acme-challenge/`, тома `certbot-conf` + `certbot-webroot`). nginx
раз в 6 ч делает `reload`, чтобы подхватить продлённый серт; certbot раз в 12 ч —
`renew`.

**Первичный выпуск серта — один раз на сервере** (DNS уже указывает на хост):

```bash
cd ~/english-tutor-web-service
./init-letsencrypt.sh   # ставит заглушку, поднимает nginx, выпускает реальный серт, reload
```

Скрипт решает «курицу-яйцо» (nginx с ssl-конфигом не стартует без серта, серт не
выпустить без nginx): сначала временный самоподписанный серт, затем настоящий.
Для отладки лимитов LE — выставить `staging=1` в скрипте. После выпуска в `.env`:
`SITE_URL=https://repetitor-diary.ru`, `SECURE_COOKIES=true`. Порты 80 и 443
должны быть открыты в фаерволе сервера.

Разовая подготовка сервера (Docker установлен): клон репозитория в
`~/english-tutor-web-service`, `cp .env.prod.example .env` и заполнить секреты
(`DEV_MODE=false`, длинный `JWT_SECRET`). Для слабого VPS — добавить swap (стек
на 0.5 ГБ живёт за счёт подкачки).

## Как устроены деньги

Неизменяемый леджер `transactions`: отметка «урок проведён» создаёт начисление
по цене с карточки родителя (снапшот — смена цены не переписывает историю),
оплаты вносятся вручную. Долг и заработок всегда считаются агрегатами,
числом нигде не хранятся. Один урок не может быть начислен дважды.

## Часовой пояс

Расписание, слоты и дайджест считаются в `TZ` из `.env` (по умолчанию
Europe/Moscow). Если занятия идут в другом поясе — поменяйте `TZ`.

Архитектурные решения и их обоснования — в `CLAUDE.md`, план развития — в `ROADMAP.md`.
