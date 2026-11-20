from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.schemas.caregiver import CaregiverAccessOut, CaregiverGrantRequest
from api.schemas.medication import MedicationOut
from database.models import CaregiverAccess, Medication, User
from services import caregiver_service, medication_service

router = APIRouter(prefix="/api/v1/caregivers", tags=["Cuidadores"])


@router.post(
    "",
    response_model=CaregiverAccessOut,
    status_code=status.HTTP_201_CREATED,
    summary="Autoriza um cuidador a acompanhar o usuário autenticado (RF12)",
)
def grant_caregiver_access(
    payload: CaregiverGrantRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CaregiverAccess:
    try:
        return caregiver_service.grant_access(db, user, payload.caregiver_telegram_user_id, payload.permission)
    except caregiver_service.CaregiverAccessError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[CaregiverAccessOut], summary="Lista os cuidadores autorizados pelo usuário")
def list_caregiver_access(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CaregiverAccess]:
    return caregiver_service.list_active_access(db, user)


@router.delete(
    "/{access_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoga o acesso de um cuidador (RF12)",
)
def revoke_caregiver_access(
    access_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    access = caregiver_service.get_owned_access(db, access_id, user)
    if access is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autorização não encontrada")
    caregiver_service.revoke_access(db, access)


@router.get(
    "/patients/{patient_user_id}/medications",
    response_model=list[MedicationOut],
    summary="Consulta os medicamentos de um paciente autorizado (acesso de cuidador, RF12)",
)
def list_patient_medications_as_caregiver(
    patient_user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Medication]:
    access = caregiver_service.find_patient_access_for_caregiver(db, patient_user_id, user)
    if access is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem autorização para este paciente")
    patient = db.get(User, patient_user_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado")
    return medication_service.list_medications(db, patient, active=True)
