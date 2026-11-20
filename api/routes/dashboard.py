from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.dashboard import DashboardOut
from core.professional_security import require_roles
from database.models import Professional
from services.dashboard_service import compute_dashboard

router = APIRouter(prefix="/api/v1/dashboard", tags=["Portal — Dashboard"])

_CLINICAL_ROLES = ("medico", "enfermeiro", "outro_profissional", "admin")


@router.get(
    "",
    response_model=DashboardOut,
    summary="Painel operacional do profissional (RF02) — pacientes, tratamentos e confirmações declaradas",
)
def get_dashboard(
    patient_id: int | None = Query(default=None),
    status: str | None = Query(default=None, description="Filtra tratamentos por status (draft/active/suspended/closed)"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    professional: Professional = Depends(require_roles(*_CLINICAL_ROLES)),
) -> DashboardOut:
    data = compute_dashboard(
        db, professional, patient_id=patient_id, status=status, start_date=start_date, end_date=end_date
    )
    return DashboardOut(**data)
