from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import LessonStatus


class HomeworkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    description: str
    is_done: bool
    created_at: datetime


class HomeworkCreate(BaseModel):
    description: str


class HomeworkUpdate(BaseModel):
    description: str | None = None
    is_done: bool | None = None


class HomeworkDoneIn(BaseModel):
    is_done: bool


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    slot_id: int | None = None
    scheduled_at: datetime
    topic: str | None
    zoom_link: str | None
    recommendation: str | None
    status: LessonStatus
    conducted_at: datetime | None
    homeworks: list[HomeworkOut]


class LessonCalendarOut(LessonOut):
    """Урок для календаря учителя: + имя ученика."""

    student_name: str


class LessonCreate(BaseModel):
    scheduled_at: datetime
    topic: str | None = None
    zoom_link: str | None = None
    recommendation: str | None = None


class LessonUpdate(BaseModel):
    scheduled_at: datetime | None = None
    topic: str | None = None
    zoom_link: str | None = None
    recommendation: str | None = None
    status: LessonStatus | None = None
