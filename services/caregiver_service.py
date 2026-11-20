"""Suporte a cuidadores autorizados (RF12)."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from database.models import CaregiverAccess, User
from services.medication_service import get_or_create_user


class CaregiverAccessError(Exception):
    """Erro de autorização ao conceder acesso de cuidador."""


def grant_access(
    db: Session, owner: User, caregiver_telegram_user_id: int, permission: str = "view"
) -> CaregiverAccess:
    caregiver = get_or_create_user(db, caregiver_telegram_user_id)
    if caregiver.id == owner.id:
        raise CaregiverAccessError("Não é possível se autorizar como cuidador de si mesmo.")

    existing = (
        db.query(CaregiverAccess)
        .filter(CaregiverAccess.user_id == owner.id, CaregiverAccess.caregiver_id == caregiver.id)
        .first()
    )
    if existing is not None:
        existing.permission = permission
        existing.revoked_at = None
        db.commit()
        db.refresh(existing)
        return existing

    access = CaregiverAccess(user_id=owner.id, caregiver_id=caregiver.id, permission=permission)
    db.add(access)
    db.commit()
    db.refresh(access)
    return access


def revoke_access(db: Session, access: CaregiverAccess) -> CaregiverAccess:
    access.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(access)
    return access


def get_owned_access(db: Session, access_id: int, owner: User) -> CaregiverAccess | None:
    access = db.get(CaregiverAccess, access_id)
    if access is None or access.user_id != owner.id:
        return None
    return access


def list_active_access(db: Session, owner: User) -> list[CaregiverAccess]:
    return (
        db.query(CaregiverAccess)
        .filter(CaregiverAccess.user_id == owner.id, CaregiverAccess.revoked_at.is_(None))
        .all()
    )


def find_patient_access_for_caregiver(db: Session, patient_user_id: int, caregiver: User) -> CaregiverAccess | None:
    return (
        db.query(CaregiverAccess)
        .filter(
            CaregiverAccess.user_id == patient_user_id,
            CaregiverAccess.caregiver_id == caregiver.id,
            CaregiverAccess.revoked_at.is_(None),
        )
        .first()
    )
