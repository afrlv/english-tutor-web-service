from pydantic import BaseModel, ConfigDict, Field

from app.models.cards import LEARNED_THRESHOLD


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    set_id: int
    front: str
    back: str
    position: int
    times_correct: int
    times_wrong: int

    @property
    def learned(self) -> bool:  # pragma: no cover — удобство, не используется в API
        return self.times_correct >= LEARNED_THRESHOLD


class CardIn(BaseModel):
    front: str = Field(min_length=1, max_length=500)
    back: str = Field(min_length=1, max_length=500)


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
    """Для списков: без самих карточек, с прогрессом."""

    id: int
    student_id: int
    lesson_id: int | None
    title: str
    total: int
    learned: int


class AnswerIn(BaseModel):
    correct: bool


def set_summary(s) -> CardSetSummary:
    return CardSetSummary(
        id=s.id,
        student_id=s.student_id,
        lesson_id=s.lesson_id,
        title=s.title,
        total=len(s.cards),
        learned=sum(1 for c in s.cards if c.times_correct >= LEARNED_THRESHOLD),
    )
