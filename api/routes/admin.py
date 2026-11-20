"""Capacidades do Administrador (seção 3): verificar solicitações de acesso profissional e
consultar a auditoria (RN32) — nunca dados clínicos de pacientes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.audit import AuditLogOut
from api.schemas.professional import ProfessionalOut, ProfessionalVerifyRequest
from core.professional_security import require_roles
from database.models import AuditLog, Professional
from services import professional_auth_service as auth_service
from services.audit_service import log_audit

router = APIRouter(prefix="/api/v1", tags=["Portal — Administração"])


@router.get(
    "/professionals",
    response_model=list[ProfessionalOut],
    summary="Lista profissionais, com filtro por status de verificação (admin)",
)
def list_professionals(
    verification_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: Professional = Depends(require_roles("admin")),
) -> list[Professional]:
    return auth_service.list_professionals(db, verification_status)


@router.post(
    "/professionals/{professional_id}/verify",
    response_model=ProfessionalOut,
    summary="Aprova, rejeita ou reabre a verificação de um profissional (admin, RF01)",
)
def verify_professional(
    professional_id: int,
    payload: ProfessionalVerifyRequest,
    db: Session = Depends(get_db),
    admin: Professional = Depends(require_roles("admin")),
) -> Professional:
    professional = db.get(Professional, professional_id)
    if professional is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profissional não encontrado")

    updated = auth_service.set_verification_status(db, professional, payload.verification_status)
    log_audit(
        db,
        admin.id,
        admin.role,
        f"professional.verification_{payload.verification_status}",
        "professional",
        updated.id,
    )
    return updated


@router.get(
    "/audit-logs",
    response_model=list[AuditLogOut],
    summary="Consulta a trilha de auditoria (RN32) — restrito a administradores",
)
def list_audit_logs(
    resource_type: str | None = Query(default=None),
    action: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _admin: Professional = Depends(require_roles("admin")),
) -> list[AuditLog]:
    query = db.query(AuditLog)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
