from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.schemas.reminder import ReminderEventOut
from database.models import ReminderEvent, User
from services import reminder_service

router = APIRouter(prefix="/api/v1/history", tags=["Histórico"])


@router.get(
    "",
    response_model=list[ReminderEventOut],
    summary="Consulta o histórico de doses com filtros por dia, semana ou mês (RF09)",
)
def get_history(
    period: Literal["day", "week", "month"] = "day",
    reference_date: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ReminderEvent]:
    return reminder_service.get_history(db, user, period, reference_date)
