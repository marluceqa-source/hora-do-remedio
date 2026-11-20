from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.schemas.medication import MedicationCreate, MedicationOut, MedicationUpdate
from database.models import Medication, User
from services import medication_service

router = APIRouter(prefix="/api/v1/medications", tags=["Medicamentos"])


def _get_owned_medication(db: Session, medication_id: int, user: User) -> Medication:
    medication = db.get(Medication, medication_id)
    if medication is None or medication.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento não encontrado")
    return medication


@router.get("", response_model=list[MedicationOut], summary="Lista os medicamentos do usuário autenticado (RN09)")
def list_medications(
    active: bool | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Medication]:
    return medication_service.list_medications(db, user, active)


@router.post(
    "",
    response_model=MedicationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um novo medicamento com seus horários (RF02)",
)
def create_medication(
    payload: MedicationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Medication:
    return medication_service.create_medication(db, user, payload)


@router.get("/{medication_id}", response_model=MedicationOut, summary="Consulta um medicamento")
def get_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Medication:
    return _get_owned_medication(db, medication_id, user)


@router.patch("/{medication_id}", response_model=MedicationOut, summary="Atualiza um medicamento (CT10)")
def update_medication(
    medication_id: int,
    payload: MedicationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Medication:
    medication = _get_owned_medication(db, medication_id, user)
    return medication_service.update_medication(db, medication, user, payload)


@router.delete(
    "/{medication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui um medicamento (RN16: requer confirmação explícita)",
)
def delete_medication(
    medication_id: int,
    confirm: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exclusão requer confirmação explícita: envie confirm=true (RN16)",
        )
    medication = _get_owned_medication(db, medication_id, user)
    medication_service.delete_medication(db, medication)
