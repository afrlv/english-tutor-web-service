from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import CancellationKind, LessonStatus


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    homework_id: int
    name: str
    file_path: str | None
    url: str | None


class AttachmentLinkIn(BaseModel):
    url: str
    name: str | None = None


class LessonAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    name: str
    file_path: str | None
    url: str | None


class HomeworkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    description: str
    is_done: bool
    student_answer: str | None = None
    checked_at: datetime | None = None
    grade: int | None = None
    attachments: list[AttachmentOut] = []
    created_at: datetime


class HomeworkCreate(BaseModel):
    description: str


class HomeworkUpdate(BaseModel):
    description: str | None = None
    is_done: bool | None = None
    # Отметка учителя «проверено» (true → ставится, false → снимается вместе с оценкой)
    is_checked: bool | None = None
    # Оценка 2–5; выставление автоматически отмечает работу проверенной
    grade: int | None = Field(default=None, ge=2, le=5)


class HomeworkStudentIn(BaseModel):
    """Что может менять ученик в своём ДЗ."""

    is_done: bool | None = None
    student_answer: str | None = None


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    slot_id: int | None = None
    scheduled_at: datetime
    duration_minutes: int = 60
    price: Decimal | None = None
    topic: str | None
    zoom_link: str | None
    recommendation: str | None
    status: LessonStatus
    conducted_at: datetime | None
    cancellation_kind: CancellationKind | None = None
    cancellation_comment: str | None = None
    rescheduled_from: datetime | None = None
    homeworks: list[HomeworkOut]
    attachments: list[LessonAttachmentOut] = []


class LessonCalendarOut(LessonOut):
    """Урок для календаря учителя: + имя ученика."""

    student_name: str


class LessonCreate(BaseModel):
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=240)
    price: Decimal | None = Field(default=None, ge=0)
    topic: str | None = None
    zoom_link: str | None = None
    recommendation: str | None = None


class LessonUpdate(BaseModel):
    # Статус меняется только явными действиями: conduct/revert/cancel/restore
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=15, le=240)
    price: Decimal | None = Field(default=None, ge=0)
    topic: str | None = None
    zoom_link: str | None = None
    recommendation: str | None = None


class LessonCancelIn(BaseModel):
    kind: CancellationKind
    comment: str | None = None
    # Для late: своя сумма начисления (по умолчанию — полная цена урока)
    charge_amount: Decimal | None = None
