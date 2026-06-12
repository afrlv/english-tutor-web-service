from datetime import time

from pydantic import BaseModel, ConfigDict, Field


class ScheduleSlotCreate(BaseModel):
    weekday: int = Field(ge=0, le=6)  # 0=Пн … 6=Вс
    start_time: time


class ScheduleSlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    weekday: int
    start_time: time
