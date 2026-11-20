from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReminderEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    medication_id: int
    scheduled_datetime: datetime
    delivery_datetime: datetime | None
    confirmed_datetime: datetime | None
    status: str
    snooze_count: int


class ReminderSnoozeRequest(BaseModel):
    minutes: Literal[5, 10, 15, 30] = Field(description="Opções de adiamento permitidas (RF08)")
