from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.students import get_student_or_404
from app.db import get_db
from app.deps import get_own_student, require_roles
from app.models import Card, CardSet, Role, Student
from app.schemas.cards import (
    AnswerIn,
    CardIn,
    CardOut,
    CardSetCreate,
    CardSetOut,
    CardSetSummary,
    CardSetUpdate,
    set_summary,
)

router = APIRouter(tags=["cards"])

teacher_only = Depends(require_roles(Role.teacher, Role.superuser))


async def get_set_or_404(set_id: int, db: AsyncSession = Depends(get_db)) -> CardSet:
    card_set = await db.get(CardSet, set_id)
    if card_set is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Набор не найден")
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
    return [set_summary(s) for s in sets]


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
        db.add(Card(set_id=card_set.id, front=card.front, back=card.back, position=i))
    await db.commit()
    await db.refresh(card_set)
    return card_set


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
        position=len(card_set.cards),
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card


@router.patch("/cards/{card_id}", response_model=CardOut, dependencies=[teacher_only])
async def update_card(
    card_id: int, data: CardIn, db: AsyncSession = Depends(get_db)
):
    card = await db.get(Card, card_id)
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Карточка не найдена")
    card.front = data.front
    card.back = data.back
    await db.commit()
    return card


@router.delete(
    "/cards/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[teacher_only],
)
async def delete_card(card_id: int, db: AsyncSession = Depends(get_db)):
    card = await db.get(Card, card_id)
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Карточка не найдена")
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
    return [set_summary(s) for s in sets]


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
    if data.correct:
        card.times_correct += 1
    else:
        card.times_wrong += 1
    await db.commit()
    return card
