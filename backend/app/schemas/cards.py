from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.cards import LEARNED_BOX, is_due

StudyDirection = Literal["front_back", "back_front", "mixed"]


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    set_id: int
    front: str
    back: str
    example: str | None
    position: int
    box: int
    due_at: datetime | None
    times_correct: int
    times_wrong: int

    @property
    def learned(self) -> bool:  # pragma: no cover — удобство, не используется в API
        return self.box >= LEARNED_BOX


class CardIn(BaseModel):
    front: str = Field(min_length=1, max_length=500)
    back: str = Field(min_length=1, max_length=500)
    example: str | None = Field(default=None, max_length=500)


class CardSetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    cards: list[CardIn] = []


class CardSetUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class CardSetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    lesson_id: int | None
    title: str
    cards: list[CardOut]


class CardSetSummary(BaseModel):
    """Для списков: без самих карточек, с прогрессом и числом карт к повтору."""

    id: int
    student_id: int
    lesson_id: int | None
    title: str
    total: int
    learned: int
    due_count: int


class AnswerIn(BaseModel):
    correct: bool


class GradeOut(BaseModel):
    """Оценка за ДЗ для ленты прогресса ученика."""

    grade: int
    at: datetime


class ProgressOut(BaseModel):
    words_total: int
    words_learned: int
    due_today: int
    study_streak: int
    best_streak: int
    recent_grades: list[GradeOut]


class StudyTodayOut(BaseModel):
    """Сборная сессия повторения по всем наборам ученика."""

    total_due: int
    cards: list[CardOut]


def set_summary(s, now: datetime) -> CardSetSummary:
    return CardSetSummary(
        id=s.id,
        student_id=s.student_id,
        lesson_id=s.lesson_id,
        title=s.title,
        total=len(s.cards),
        learned=sum(1 for c in s.cards if c.box >= LEARNED_BOX),
        due_count=sum(1 for c in s.cards if is_due(c, now)),
    )
