from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.schemas.schedule import ScheduleOut
from database.models import Medication, Schedule, User

router = APIRouter(prefix="/api/v1/schedules", tags=["Agendamentos"])


@router.get("", response_model=list[ScheduleOut], summary="Consulta os agendamentos do usuário autenticado")
def list_schedules(
    medication_id: int | None = Query(default=None, description="Filtra por medicamento"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Schedule]:
    query = db.query(Schedule).join(Medication).filter(Medication.user_id == user.id)
    if medication_id is not None:
        query = query.filter(Schedule.medication_id == medication_id)
    return query.all()
