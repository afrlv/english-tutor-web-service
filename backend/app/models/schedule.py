from datetime import time

from sqlalchemy import Boolean, ForeignKey, SmallInteger, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin


class ScheduleSlot(Base, CreatedAtMixin):
    """Повторяющийся слот расписания: «каждый вторник в 16:00» (в TZ из настроек).

    Из слотов материализуются реальные уроки на generate_weeks вперёд.
    Удаление слота — soft (is_active=False), чтобы прошедшие уроки
    сохранили ссылку на происхождение.
    """

    __tablename__ = "schedule_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    weekday: Mapped[int] = mapped_column(SmallInteger)  # 0=Пн … 6=Вс
    start_time: Mapped[time] = mapped_column(Time)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
