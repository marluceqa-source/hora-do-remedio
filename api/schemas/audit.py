from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int | None
    actor_role: str
    action: str
    resource_type: str
    resource_id: int | None
    timestamp: datetime
    correlation_id: str
