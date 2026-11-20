from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CaregiverGrantRequest(BaseModel):
    caregiver_telegram_user_id: int
    permission: Literal["view", "manage"] = "view"


class CaregiverAccessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    caregiver_id: int
    permission: str
    authorized_at: datetime
    revoked_at: datetime | None
