"""RN32: toda operação sensível do portal deve ser auditável."""

import uuid

from sqlalchemy.orm import Session

from database.models import AuditLog


def log_audit(
    db: Session,
    actor_id: int | None,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    correlation_id: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        correlation_id=correlation_id or str(uuid.uuid4()),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
