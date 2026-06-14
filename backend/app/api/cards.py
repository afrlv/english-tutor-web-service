import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.students import get_student_or_404
from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user, get_own_student, owns_student, require_roles
from app.models import Card, CardSet, Homework, Lesson, Role, Student, User
from app.models.cards import LEARNED_BOX, apply_answer, is_due
from app.schemas.cards import (
    AnswerIn,
    CardIn,
    CardOut,
    CardSetCreate,
    CardSetOut,
    CardSetSummary,
    CardSetUpdate,
    GradeOut,
    ProgressOut,
    StudyDirection,
    StudyTodayOut,
    set_summary,
)

router = APIRouter(tags=["cards"])

teacher_only = Depends(require_roles(Role.teacher, Role.superuser))


def _now() -> datetime:
    return datetime.now(ZoneInfo(get_settings().tz))


def _study_order(cards: list[Card], now: datetime) -> list[Card]:
    """Слабые-первыми: сортируем по коробке и сроку, шаффлим внутри коробки."""
    due = [c for c in cards if is_due(c, now)]
    pool = due or list(cards)  # если к повтору ничего нет — учим весь набор
    by_box: dict[int, list[Card]] = {}
    for c in pool:
        by_box.setdefault(c.box, []).append(c)
    ordered: list[Card] = []
    for box in sorted(by_box):
        group = by_box[box]
        random.shuffle(group)
        ordered.extend(group)
    return ordered


async def _assert_owns_student(
    student_id: int, user: User, db: AsyncSession, msg: str
) -> None:
    owner = await db.get(Student, student_id)
    if owner is None or not owns_student(user, owner):
        raise HTTPException(status.HTTP_404_NOT_FOUND, msg)


async def get_set_or_404(
    set_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CardSet:
    card_set = await db.get(CardSet, set_id)
    if card_set is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Набор не найден")
    await _assert_owns_student(card_set.student_id, user, db, "Набор не найден")
    return card_set


# --- Учитель ---


@router.get(
    "/students/{student_id}/card-sets",
    response_model=list[CardSetSummary],
    dependencies=[teacher_only],
)
async def list_sets(
    student: Student = Depends(get_student_or_404),
    db: AsyncSession = Depends(get_db),
):
    sets = (
        await db.scalars(
            select(CardSet).where(CardSet.student_id == student.id).order_by(CardSet.id)
        )
    ).all()
    now = _now()
    return [set_summary(s, now) for s in sets]


@router.post(
    "/students/{student_id}/card-sets",
    response_model=CardSetOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[teacher_only],
)
async def create_set(
    data: CardSetCreate,
    student: Student = Depends(get_student_or_404),
    db: AsyncSession = Depends(get_db),
):
    card_set = CardSet(student_id=student.id, title=data.title)
    db.add(card_set)
    await db.flush()
    for i, card in enumerate(data.cards):
        db.add(
            Card(
                set_id=card_set.id,
                front=card.front,
                back=card.back,
                example=card.example,
                position=i,
            )
        )
    await db.commit()
    await db.refresh(card_set)
    return card_set


async def get_lesson_or_404(
    lesson_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Lesson:
    lesson = await db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Урок не найден")
    await _assert_owns_student(lesson.student_id, user, db, "Урок не найден")
    return lesson


@router.get(
    "/lessons/{lesson_id}/card-sets",
    response_model=list[CardSetSummary],
    dependencies=[teacher_only],
)
async def list_lesson_sets(
    lesson: Lesson = Depends(get_lesson_or_404),
    db: AsyncSession = Depends(get_db),
):
    sets = (
        await db.scalars(
            select(CardSet).where(CardSet.lesson_id == lesson.id).order_by(CardSet.id)
        )
    ).all()
    now = _now()
    return [set_summary(s, now) for s in sets]


@router.post(
    "/lessons/{lesson_id}/card-sets",
    response_model=CardSetOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[teacher_only],
)
async def create_lesson_set(
    data: CardSetCreate,
    lesson: Lesson = Depends(get_lesson_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Набор для урока — принадлежит ученику урока, привязан к уроку."""
    card_set = CardSet(student_id=lesson.student_id, lesson_id=lesson.id, title=data.title)
    db.add(card_set)
    await db.flush()
    for i, card in enumerate(data.cards):
        db.add(
            Card(
                set_id=card_set.id,
                front=card.front,
                back=card.back,
                example=card.example,
                position=i,
            )
        )
    await db.commit()
    await db.refresh(card_set)
    return card_set


@router.post(
    "/lessons/{lesson_id}/card-sets/{set_id}/attach",
    response_model=CardSetOut,
    dependencies=[teacher_only],
)
async def attach_set_to_lesson(
    set_id: int,
    lesson: Lesson = Depends(get_lesson_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Привязывает отвязанный набор ученика к уроку (повторная привязка)."""
    card_set = await db.get(CardSet, set_id)
    if card_set is None or card_set.student_id != lesson.student_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Набор не найден")
    if card_set.lesson_id is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Набор уже привязан к уроку"
        )
    card_set.lesson_id = lesson.id
    await db.commit()
    await db.refresh(card_set)
    return card_set


@router.post(
    "/card-sets/{set_id}/copy",
    response_model=CardSetOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[teacher_only],
)
async def copy_set(
    card_set: CardSet = Depends(get_set_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Копия набора тому же ученику: карточки без SRS-прогресса, набор отвязан."""
    copy = CardSet(
        student_id=card_set.student_id,
        lesson_id=None,  # копия общая — потом можно привязать к нужному уроку
        title=f"{card_set.title} (копия)",
    )
    db.add(copy)
    await db.flush()
    for i, card in enumerate(card_set.cards):
        db.add(
            Card(
                set_id=copy.id,
                front=card.front,
                back=card.back,
                example=card.example,
                position=i,
            )
        )
    await db.commit()
    await db.refresh(copy)
    return copy


@router.get("/card-sets/{set_id}", response_model=CardSetOut, dependencies=[teacher_only])
async def get_set(card_set: CardSet = Depends(get_set_or_404)):
    return card_set


@router.patch(
    "/card-sets/{set_id}", response_model=CardSetOut, dependencies=[teacher_only]
)
async def rename_set(
    data: CardSetUpdate,
    card_set: CardSet = Depends(get_set_or_404),
    db: AsyncSession = Depends(get_db),
):
    card_set.title = data.title
    await db.commit()
    return card_set


@router.delete(
    "/card-sets/{set_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[teacher_only],
)
async def delete_set(
    card_set: CardSet = Depends(get_set_or_404),
    db: AsyncSession = Depends(get_db),
):
    await db.delete(card_set)
    await db.commit()


@router.post(
    "/card-sets/{set_id}/cards",
    response_model=CardOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[teacher_only],
)
async def add_card(
    data: CardIn,
    card_set: CardSet = Depends(get_set_or_404),
    db: AsyncSession = Depends(get_db),
):
    card = Card(
        set_id=card_set.id,
        front=data.front,
        back=data.back,
        example=data.example,
        position=len(card_set.cards),
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card


async def get_card_or_404(
    card_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Card:
    card = await db.get(Card, card_id)
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Карточка не найдена")
    card_set = await db.get(CardSet, card.set_id)
    await _assert_owns_student(card_set.student_id, user, db, "Карточка не найдена")
    return card


@router.patch("/cards/{card_id}", response_model=CardOut, dependencies=[teacher_only])
async def update_card(
    data: CardIn,
    card: Card = Depends(get_card_or_404),
    db: AsyncSession = Depends(get_db),
):
    card.front = data.front
    card.back = data.back
    card.example = data.example
    await db.commit()
    return card


@router.delete(
    "/cards/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[teacher_only],
)
async def delete_card(
    card: Card = Depends(get_card_or_404),
    db: AsyncSession = Depends(get_db),
):
    await db.delete(card)
    await db.commit()


# --- Ученик ---


@router.get("/me/card-sets", response_model=list[CardSetSummary])
async def my_sets(
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    sets = (
        await db.scalars(
            select(CardSet).where(CardSet.student_id == student.id).order_by(CardSet.id)
        )
    ).all()
    now = _now()
    return [set_summary(s, now) for s in sets]


@router.get("/me/lessons/{lesson_id}/card-sets", response_model=list[CardSetSummary])
async def my_lesson_sets(
    lesson_id: int,
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    sets = (
        await db.scalars(
            select(CardSet)
            .where(CardSet.lesson_id == lesson_id, CardSet.student_id == student.id)
            .order_by(CardSet.id)
        )
    ).all()
    now = _now()
    return [set_summary(s, now) for s in sets]


@router.get("/me/card-sets/{set_id}", response_model=CardSetOut)
async def my_set(
    set_id: int,
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    card_set = await db.get(CardSet, set_id)
    if card_set is None or card_set.student_id != student.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Набор не найден")
    return card_set


@router.get("/me/card-sets/{set_id}/study", response_model=list[CardOut])
async def study_set(
    set_id: int,
    direction: StudyDirection = "front_back",  # noqa: ARG001 — направление выбирает фронт
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    """Карточки набора к повтору, слабые-первыми; направление обрабатывает фронт."""
    card_set = await db.get(CardSet, set_id)
    if card_set is None or card_set.student_id != student.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Набор не найден")
    return _study_order(list(card_set.cards), _now())


@router.get("/me/study/today", response_model=StudyTodayOut)
async def study_today(
    limit: int = Query(default=0, ge=0),
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    """Сборная сессия по всем наборам ученика: карточки к повтору, слабые-первыми."""
    now = _now()
    cards = (
        await db.scalars(
            select(Card)
            .join(CardSet, CardSet.id == Card.set_id)
            .where(CardSet.student_id == student.id)
        )
    ).all()
    due = [c for c in cards if is_due(c, now)]
    ordered = _study_order(due, now) if due else []
    cap = limit or get_settings().study_daily_limit
    return StudyTodayOut(total_due=len(due), cards=ordered[:cap])


@router.get("/me/progress", response_model=ProgressOut)
async def my_progress(
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    now = _now()
    cards = (
        await db.scalars(
            select(Card)
            .join(CardSet, CardSet.id == Card.set_id)
            .where(CardSet.student_id == student.id)
        )
    ).all()
    graded = (
        await db.execute(
            select(Homework.grade, Homework.checked_at)
            .join(Lesson, Lesson.id == Homework.lesson_id)
            .where(
                Lesson.student_id == student.id,
                Homework.grade.is_not(None),
                Homework.checked_at.is_not(None),
            )
            .order_by(Homework.checked_at.desc())
            .limit(10)
        )
    ).all()
    return ProgressOut(
        words_total=len(cards),
        words_learned=sum(1 for c in cards if c.box >= LEARNED_BOX),
        due_today=sum(1 for c in cards if is_due(c, now)),
        study_streak=student.study_streak,
        best_streak=student.best_streak,
        recent_grades=[GradeOut(grade=g, at=at) for g, at in graded],
    )


@router.post("/me/cards/{card_id}/answer", response_model=CardOut)
async def answer_card(
    card_id: int,
    data: AnswerIn,
    student: Student = Depends(get_own_student),
    db: AsyncSession = Depends(get_db),
):
    card = await db.scalar(
        select(Card)
        .join(CardSet, CardSet.id == Card.set_id)
        .where(Card.id == card_id, CardSet.student_id == student.id)
    )
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Карточка не найдена")
    now = _now()
    apply_answer(card, data.correct, now)
    _bump_streak(student, now)
    await db.commit()
    return card


def _bump_streak(student: Student, now: datetime) -> None:
    """Серия: +1 если занимался вчера, иначе сброс на 1; раз в день."""
    today = now.date()
    if student.last_study_date == today:
        return
    if student.last_study_date == today - timedelta(days=1):
        student.study_streak += 1
    else:
        student.study_streak = 1
    student.best_streak = max(student.best_streak, student.study_streak)
    student.last_study_date = today
