from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.patient import PatientCreateRequest, PatientInviteOut, PatientOut
from api.schemas.reminder import ReminderEventOut
from api.schemas.treatment import TreatmentMedicationCreateRequest, TreatmentMedicationOut
from core.professional_security import require_roles
from database.models import Patient, Professional, ReminderEvent, TreatmentMedication
from services import patient_service, reminder_service, treatment_service
from services.audit_service import log_audit

router = APIRouter(prefix="/api/v1/patients", tags=["Portal — Pacientes"])

_CLINICAL_ROLES = ("medico", "enfermeiro", "outro_profissional")


def _get_owned_patient(db: Session, professional: Professional, patient_id: int) -> Patient:
    patient = patient_service.get_authorized_patient(db, professional, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado ou sem vínculo autorizado")
    return patient


@router.get("", response_model=list[PatientOut], summary="Lista os pacientes autorizados do profissional (RN22)")
def list_patients(
    db: Session = Depends(get_db),
    professional: Professional = Depends(require_roles(*_CLINICAL_ROLES, "admin")),
) -> list[Patient]:
    return patient_service.list_authorized_patients(db, professional)


@router.post(
    "",
    response_model=PatientOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um paciente (RF03) — quem cadastra fica automaticamente vinculado",
)
def create_patient(
    payload: PatientCreateRequest,
    db: Session = Depends(get_db),
    professional: Professional = Depends(require_roles(*_CLINICAL_ROLES)),
) -> Patient:
    try:
        patient = patient_service.create_patient(
            db,
            professional,
            full_name=payload.full_name,
            internal_identifier=payload.internal_identifier,
            birth_date=payload.birth_date,
            contact=payload.contact,
        )
    except patient_service.DuplicateInternalIdentifierError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Já existe um paciente com este identificador interno"
        ) from exc

    log_audit(db, professional.id, professional.role, "patient.create", "patient", patient.id)
    return patient


@router.get("/{patient_id}", response_model=PatientOut, summary="Consulta um paciente autorizado (RN22)")
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    professional: Professional = Depends(require_roles(*_CLINICAL_ROLES, "admin")),
) -> Patient:
    return _get_owned_patient(db, professional, patient_id)


@router.post(
    "/{patient_id}/invites",
    response_model=PatientInviteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Gera um convite único e temporário para vincular o paciente ao Telegram (RF04)",
)
def create_patient_invite(
    patient_id: int,
    db: Session = Depends(get_db),
    professional: Professional = Depends(require_roles(*_CLINICAL_ROLES)),
) -> PatientInviteOut:
    patient = _get_owned_patient(db, professional, patient_id)
    try:
        invite, raw_token = patient_service.create_invite(db, professional, patient)
    except patient_service.PatientAlreadyLinkedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Paciente já vinculado ao Telegram") from exc

    log_audit(db, professional.id, professional.role, "patient.invite_created", "patient", patient.id)

    deep_link = patient_service.build_telegram_deep_link(raw_token)
    instructions = (
        f"Peça para o paciente abrir o link ou, no bot, enviar: /start {raw_token}"
        if deep_link is None
        else "Peça para o paciente tocar no link ou escanear o QR Code gerado a partir dele."
    )
    return PatientInviteOut(
        invite_id=invite.id,
        token=raw_token,
        telegram_deep_link=deep_link,
        instructions=instructions,
        expires_at=invite.expires_at,
    )


@router.get(
    "/{patient_id}/medications",
    response_model=list[TreatmentMedicationOut],
    summary="Lista os medicamentos/tratamentos cadastrados para o paciente (RF05)",
)
def list_patient_treatment_medications(
    patient_id: int,
    db: Session = Depends(get_db),
    professional: Professional = Depends(require_roles(*_CLINICAL_ROLES, "admin")),
) -> list[TreatmentMedication]:
    patient = _get_owned_patient(db, professional, patient_id)
    return treatment_service.list_treatment_medications(db, patient)


@router.post(
    "/{patient_id}/medications",
    response_model=TreatmentMedicationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um medicamento/esquema terapêutico como rascunho (RF05, RN25)",
)
def create_patient_treatment_medication(
    patient_id: int,
    payload: TreatmentMedicationCreateRequest,
    db: Session = Depends(get_db),
    professional: Professional = Depends(require_roles(*_CLINICAL_ROLES)),
) -> TreatmentMedication:
    patient = _get_owned_patient(db, professional, patient_id)
    treatment_medication = treatment_service.create_treatment_medication(
        db,
        professional,
        patient,
        medication_name=payload.medication_name,
        active_ingredient=payload.active_ingredient,
        presentation=payload.presentation,
        route=payload.route,
        dosage=payload.dosage,
        dosage_unit=payload.dosage_unit,
        quantity_per_administration=payload.quantity_per_administration,
        frequency_description=payload.frequency_description,
        instructions=payload.instructions,
        start_date=payload.start_date,
        end_date=payload.end_date,
        photo_path=payload.photo_path,
        schedules=payload.schedules,
    )
    log_audit(db, professional.id, professional.role, "treatment_medication.create", "treatment_medication", treatment_medication.id)
    return treatment_medication


@router.get(
    "/{patient_id}/history",
    response_model=list[ReminderEventOut],
    summary="Consulta o histórico de doses do paciente (RF08) — RN12: ausência de resposta não prova que não tomou",
)
def get_patient_history(
    patient_id: int,
    period: Literal["day", "week", "month"] = "week",
    reference_date: date | None = None,
    db: Session = Depends(get_db),
    professional: Professional = Depends(require_roles(*_CLINICAL_ROLES, "admin")),
) -> list[ReminderEvent]:
    patient = _get_owned_patient(db, professional, patient_id)
    if patient.user is None:
        return []
    return reminder_service.get_history(db, patient.user, period, reference_date)
