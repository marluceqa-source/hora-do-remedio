"""Cadastro de pacientes e vínculo com o Telegram (RF03, RF04)."""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from core.config import get_settings
from core.professional_security import generate_opaque_token, hash_opaque_token
from database.models import Patient, PatientInvitation, PatientProfessionalLink, Professional, User
from services.medication_service import get_or_create_user


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PatientServiceError(Exception):
    """Erro genérico de cadastro/vínculo de paciente."""


class DuplicateInternalIdentifierError(PatientServiceError):
    pass


class PatientAlreadyLinkedError(PatientServiceError):
    pass


class InvalidInviteError(PatientServiceError):
    pass


def create_patient(
    db: Session,
    professional: Professional,
    *,
    full_name: str,
    internal_identifier: str,
    birth_date: date | None = None,
    contact: str | None = None,
) -> Patient:
    if db.query(Patient).filter(Patient.internal_identifier == internal_identifier).first() is not None:
        raise DuplicateInternalIdentifierError()

    patient = Patient(
        full_name=full_name,
        internal_identifier=internal_identifier,
        birth_date=birth_date,
        contact=contact,
        created_by_professional_id=professional.id,
    )
    db.add(patient)
    db.flush()

    # RF03/RN22: quem cadastra já fica com vínculo ativo — é assim que passa a "ver" o paciente.
    link = PatientProfessionalLink(
        patient_id=patient.id,
        professional_id=professional.id,
        relationship_type="responsavel",
        authorization_status="active",
    )
    db.add(link)
    db.commit()
    db.refresh(patient)
    return patient


def list_authorized_patients(db: Session, professional: Professional) -> list[Patient]:
    return (
        db.query(Patient)
        .join(PatientProfessionalLink, PatientProfessionalLink.patient_id == Patient.id)
        .filter(
            PatientProfessionalLink.professional_id == professional.id,
            PatientProfessionalLink.authorization_status == "active",
        )
        .order_by(Patient.full_name)
        .all()
    )


def get_authorized_patient(db: Session, professional: Professional, patient_id: int) -> Patient | None:
    return (
        db.query(Patient)
        .join(PatientProfessionalLink, PatientProfessionalLink.patient_id == Patient.id)
        .filter(
            Patient.id == patient_id,
            PatientProfessionalLink.professional_id == professional.id,
            PatientProfessionalLink.authorization_status == "active",
        )
        .first()
    )


def create_invite(db: Session, professional: Professional, patient: Patient) -> tuple[PatientInvitation, str]:
    """Convite único e temporário (RF04, RN23/RN24). Retorna (registro, token em claro —
    só existe aqui; o banco guarda apenas o hash)."""
    if patient.telegram_link_status == "linked":
        raise PatientAlreadyLinkedError()

    settings = get_settings()
    raw_token = generate_opaque_token()
    invite = PatientInvitation(
        patient_id=patient.id,
        created_by_professional_id=professional.id,
        token_hash=hash_opaque_token(raw_token),
        expires_at=_utcnow() + timedelta(minutes=settings.patient_invite_expire_minutes),
    )
    db.add(invite)
    patient.telegram_link_status = "invited"
    db.commit()
    db.refresh(invite)
    return invite, raw_token


def build_telegram_deep_link(raw_token: str) -> str | None:
    settings = get_settings()
    if not settings.telegram_bot_username:
        return None
    return f"https://t.me/{settings.telegram_bot_username}?start={raw_token}"


def find_valid_invite(db: Session, raw_token: str) -> PatientInvitation | None:
    invite = db.query(PatientInvitation).filter(PatientInvitation.token_hash == hash_opaque_token(raw_token)).first()
    return _if_still_valid(invite)


def get_valid_invite_by_id(db: Session, invite_id: int) -> PatientInvitation | None:
    """Revalida pelo id no momento da confirmação (o token bruto não precisa trafegar de novo
    pelo callback_data do botão)."""
    return _if_still_valid(db.get(PatientInvitation, invite_id))


def _if_still_valid(invite: PatientInvitation | None) -> PatientInvitation | None:
    if invite is None or invite.consumed_at is not None or invite.revoked_at is not None:
        return None
    if invite.expires_at < _utcnow():
        return None
    return invite


def confirm_invite_link(db: Session, invite: PatientInvitation, telegram_user_id: int) -> Patient:
    """RF04 pontos 6-7: conclui o vínculo após a confirmação do paciente no bot."""
    user = get_or_create_user(db, telegram_user_id)
    patient = db.get(Patient, invite.patient_id)
    if patient is None:
        raise InvalidInviteError()

    existing_link = db.query(Patient).filter(Patient.user_id == user.id, Patient.id != patient.id).first()
    if existing_link is not None:
        # Esta conta do Telegram já está vinculada a outro registro de paciente.
        raise PatientAlreadyLinkedError()

    patient.user_id = user.id
    patient.telegram_link_status = "linked"
    invite.consumed_at = _utcnow()
    db.commit()
    db.refresh(patient)
    return patient
