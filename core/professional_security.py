"""Primitivas de segurança do portal de profissionais (RF01).

Deliberadamente separado de `core/security.py` (JWT do bot/paciente): são dois públicos e
dois conjuntos de segredos diferentes — um vazamento de um não deve comprometer o outro.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
import pyotp
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from core.config import get_settings
from database.connection import get_db
from database.models import Professional

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_cookie_scheme = APIKeyCookie(
    name=get_settings().professional_session_cookie_name,
    auto_error=False,
    description="Cookie httpOnly de sessão, emitido após login + MFA do profissional.",
)

PRE_AUTH_PURPOSE_MFA_SETUP = "mfa_setup"
PRE_AUTH_PURPOSE_MFA_VERIFY = "mfa_verify"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name="Hora do Remédio")


def verify_totp_code(secret: str, code: str) -> bool:
    return pyotp.totp.TOTP(secret).verify(code, valid_window=1)


def generate_opaque_token() -> str:
    """Token aleatório de alta entropia para sessões, convites e reset de senha."""
    return secrets.token_urlsafe(32)


def hash_opaque_token(token: str) -> str:
    """Hash determinístico (não precisa de salt: a entrada já tem entropia suficiente e é
    descartada após o uso) — permite localizar o token por hash sem guardar o valor em claro."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_pre_auth_token(professional_id: int, purpose: str) -> str:
    settings = get_settings()
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=settings.professional_mfa_pre_auth_expire_minutes)
    payload = {"sub": str(professional_id), "purpose": purpose, "exp": expire_at}
    return jwt.encode(payload, settings.professional_session_secret_key, algorithm="HS256")


def decode_pre_auth_token(token: str, expected_purpose: str) -> int:
    """Retorna o professional_id, ou levanta jwt.PyJWTError/ValueError se inválido/expirado/purpose errado."""
    settings = get_settings()
    payload = jwt.decode(token, settings.professional_session_secret_key, algorithms=["HS256"])
    if payload.get("purpose") != expected_purpose:
        raise ValueError("Finalidade do token de pré-autenticação não corresponde ao esperado")
    return int(payload["sub"])


def get_current_professional(
    session_token: str | None = Depends(_cookie_scheme),
    db: Session = Depends(get_db),
) -> Professional:
    from services.professional_auth_service import get_professional_from_session_token

    professional = get_professional_from_session_token(db, session_token)
    if professional is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida, expirada ou ausente")
    return professional


def require_roles(*allowed_roles: str):
    """RBAC (seção 3): só deixa passar profissionais cujo papel esteja em `allowed_roles`."""

    def _dependency(professional: Professional = Depends(get_current_professional)) -> Professional:
        if professional.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Seu papel não tem permissão para este recurso"
            )
        return professional

    return _dependency
