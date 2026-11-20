"""Edição, ativação, suspensão e histórico de versões de tratamentos (RF07).

Nota de nomenclatura: o prompt do portal sugere `PATCH /api/v1/medications/{id}` para isto,
mas esse caminho já é usado pelo CRUD de medicamentos do próprio paciente via bot/API (Etapa 2
do projeto original) — por instrução explícita de "preservar os endpoints existentes", usamos
`/api/v1/treatment-medications/{id}` aqui para não colidir.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.treatment import TreatmentMedicationOut, TreatmentMedicationUpdateRequest
from core.professional_security import require_roles
from database.models import Professional, TreatmentMedication
from services import patient_service, treatment_service
from services.audit_service import log_audit
from services.notification_service import send_medication_registered_notification

router = APIRouter(prefix="/api/v1/treatment-medications", tags=["Portal — Tratamentos"])

_CLINICAL_ROLES = ("medico", "enfermeiro", "outro_profissional")


def _get_owned_treatment_medication(
    db: Session, professional: Professional, treatment_medication_id: int
) -> TreatmentMedication:
    treatment_medication = db.get(TreatmentMedication, treatment_medication_id)
    if treatment_medication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tratamento não encontrado")
    patient = treatment_medication.treatment_plan.patient
    if patient_service.get_authorized_patient(db, professional, patient.id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tratamento não encontrado")
    return treatment_medication


@router.patch(
    "/{treatment_medication_id}",
    response_model=TreatmentMedicationOut,
    summary="Atualiza um medicamento/esquema; cria nova versão se já estiver ativo (RF07, RN27)",
)
def update_treatment_medication(
    treatment_medication_id: int,
    payload: TreatmentMedicationUpdateRequest,
    db: Session = Depends(get_db),
    professional: Professional = Depends(require_roles(*_CLINICAL_ROLES)),
) -> TreatmentMedication:
    treatment_medication = _get_owned_treatment_medication(db, professional, treatment_medication_id)
    fields = payload.model_dump(exclude_unset=True, exclude={"schedules"})
    try:
        updated = treatment_service.update_treatment_medication(
            db, treatment_medication, fields=fields, schedules=payload.schedules
        )
    except treatment_service.InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    log_audit(
        db, professional.id, professional.role, "treatment_medication.update", "treatment_medication", updated.id
    )
    return updated


@router.post(
    "/{treatment_medication_id}/activate",
    response_model=TreatmentMedicationOut,
    summary="Ativa um plano validado (RF06, RN20, RN26) — requer paciente já vinculado ao Telegram",
)
def activate_treatment_medication(
    treatment_medication_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    professional: Professional = Depends(require_roles(*_CLINICAL_ROLES)),
) -> TreatmentMedication:
    treatment_medication = _get_owned_treatment_medication(db, professional, treatment_medication_id)
    try:
        activated = treatment_service.activate_treatment_medication(db, professional, treatment_medication)
    except treatment_service.InsufficientRoleError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Só um médico pode ativar um tratamento (RN20)"
        ) from exc
    except treatment_service.PatientNotLinkedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="O paciente ainda não está vinculado ao Telegram"
        ) from exc
    except treatment_service.InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    log_audit(
        db, professional.id, professional.role, "treatment_medication.activate", "treatment_medication", activated.id
    )
    # RF06 ponto 5: notificação ao paciente roda depois da resposta HTTP (não trava o pedido
    # do profissional esperando a chamada de rede ao Telegram).
    background_tasks.add_task(send_medication_registered_notification, activated.linked_medication_id)
    return activated


@router.post(
    "/{treatment_medication_id}/suspend",
    response_model=TreatmentMedicationOut,
    summary="Suspende um tratamento ativo (RF07, RN28)",
)
def suspend_treatment_medication(
    treatment_medication_id: int,
    db: Session = Depends(get_db),
    professional: Professional = Depends(require_roles(*_CLINICAL_ROLES)),
) -> TreatmentMedication:
    treatment_medication = _get_owned_treatment_medication(db, professional, treatment_medication_id)
    try:
        suspended = treatment_service.suspend_treatment_medication(db, treatment_medication)
    except treatment_service.InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    log_audit(
        db, professional.id, professional.role, "treatment_medication.suspend", "treatment_medication", suspended.id
    )
    return suspended


@router.get(
    "/{treatment_medication_id}/versions",
    response_model=list[TreatmentMedicationOut],
    summary="Consulta as versões anteriores de um medicamento/esquema (RF07)",
)
def get_treatment_medication_versions(
    treatment_medication_id: int,
    db: Session = Depends(get_db),
    professional: Professional = Depends(require_roles(*_CLINICAL_ROLES, "admin")),
) -> list[TreatmentMedication]:
    treatment_medication = _get_owned_treatment_medication(db, professional, treatment_medication_id)
    return treatment_service.get_version_chain(db, treatment_medication)
