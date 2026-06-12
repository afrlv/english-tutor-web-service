import asyncio
import os

# Тестовая БД (teacher_test) подменяется ДО импорта app.*, чтобы Settings её подхватили
_DEFAULT_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://teacher:teacher@localhost:5432/teacher"
)
_TEST_URL = _DEFAULT_URL.rsplit("/", 1)[0] + "/teacher_test"
os.environ["DATABASE_URL"] = _TEST_URL
os.environ["SCHEDULER_ENABLED"] = "false"

import asyncpg  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, Parent, Role, Student, User  # noqa: E402
from app.security import hash_password  # noqa: E402

test_engine = create_async_engine(_TEST_URL, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def _override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


async def _ensure_test_db() -> None:
    admin_url = _DEFAULT_URL.replace("+asyncpg", "")
    conn = await asyncpg.connect(admin_url)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'teacher_test'"
        )
        if not exists:
            await conn.execute("CREATE DATABASE teacher_test")
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
def _test_db():
    asyncio.run(_ensure_test_db())


@pytest_asyncio.fixture(autouse=True)
async def _schema(_test_db):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class FakeEmailSender:
    def __init__(self):
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))


@pytest.fixture(autouse=True)
def fake_email(monkeypatch) -> FakeEmailSender:
    fake = FakeEmailSender()
    monkeypatch.setattr("app.services.users.get_email_sender", lambda: fake)
    monkeypatch.setattr("app.services.digest.get_email_sender", lambda: fake)
    monkeypatch.setattr("app.services.reminders.get_email_sender", lambda: fake)
    return fake


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


PASSWORD = "test-password-1"


@pytest_asyncio.fixture
async def seed_users():
    """Стандартный набор: суперюзер, учитель, ученик (с карточкой), родитель (цена 1500)."""
    async with TestSession() as db:
        users = {}
        for key, role in [
            ("superuser", Role.superuser),
            ("teacher", Role.teacher),
            ("student", Role.student),
            ("parent", Role.parent),
        ]:
            user = User(
                email=f"{key}@test.ru",
                login=f"{key}@test.ru",
                hashed_password=hash_password(PASSWORD),
                full_name=f"Тест {key}",
                role=role,
            )
            db.add(user)
            users[key] = user
        await db.flush()
        student = Student(user_id=users["student"].id)
        db.add(student)
        await db.flush()
        parent = Parent(
            user_id=users["parent"].id, student_id=student.id, lesson_price=1500
        )
        db.add(parent)
        await db.commit()
        return {
            "users": users,
            "student_id": student.id,
            "parent_id": parent.id,
        }


async def login(client: AsyncClient, email: str) -> None:
    resp = await client.post("/api/auth/login", json={"login": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
