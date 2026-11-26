"""Autenticação de profissionais do portal (RF01): senha, bloqueio por tentativas, MFA (TOTP)
e sessões revogáveis no servidor.

Mantido separado da autenticação do bot/API (RN09 cobre o paciente). A regra de negócio aqui
é **RN19** — "apenas profissionais autorizados poderão registrar planos associados a
pacientes" —; o resto (MFA, bloqueio, expiração de sessão) vem da seção 18 do prompt do
portal, que trata de segurança, e não de uma RN própria.

Este módulo já citou RN30 por engano. RN30 é "o bot não deverá alterar prescrições por conta
própria", e está em `bot/handlers/patients.py` — nada a ver com sessão."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from core.config import get_settings
from core.professional_security import (
    PRE_AUTH_PURPOSE_MFA_SETUP,
    PRE_AUTH_PURPOSE_MFA_VERIFY,
    create_pre_auth_token,
    decode_pre_auth_token,
    generate_opaque_token,
    generate_totp_secret,
    hash_opaque_token,
    hash_password,
    totp_provisioning_uri,
    verify_password,
    verify_totp_code,
)
from database.models import Professional, ProfessionalPasswordResetToken, ProfessionalSession


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ProfessionalAuthError(Exception):
    """Erro genérico de autenticação do portal."""


class EmailAlreadyRegisteredError(ProfessionalAuthError):
    pass


class InvalidCredentialsError(ProfessionalAuthError):
    pass


class AccountLockedError(ProfessionalAuthError):
    def __init__(self, locked_until: datetime) -> None:
        self.locked_until = locked_until
        super().__init__(f"Conta bloqueada até {locked_until.isoformat()} (RF01)")


class InvalidMfaCodeError(ProfessionalAuthError):
    pass


class InvalidOrExpiredTokenError(ProfessionalAuthError):
    pass


@dataclass
class LoginChallenge:
    """Resultado da 1ª etapa do login: a senha está correta, mas a sessão só é emitida
    depois da 2ª etapa de MFA (configurar, na primeira vez, ou verificar, nas seguintes)."""

    professional_id: int
    pre_auth_token: str
    purpose: str


def register_professional(
    db: Session,
    *,
    full_name: str,
    email: str,
    password: str,
    role: str,
    profession: str,
    council_type: str | None = None,
    council_number: str | None = None,
    council_state: str | None = None,
    institution: str | None = None,
) -> Professional:
    if db.query(Professional).filter(Professional.email == email).first() is not None:
        raise EmailAlreadyRegisteredError()

    professional = Professional(
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        profession=profession,
        council_type=council_type,
        council_number=council_number,
        council_state=council_state,
        institution=institution,
        verification_status="pending",
    )
    db.add(professional)
    db.commit()
    db.refresh(professional)
    return professional


def authenticate_password(db: Session, email: str, password: str) -> LoginChallenge:
    settings = get_settings()
    professional = db.query(Professional).filter(Professional.email == email).first()
    if professional is None:
        # Não diferenciar "e-mail não existe" de "senha errada" evita enumeração de contas.
        raise InvalidCredentialsError()

    if professional.locked_until is not None and professional.locked_until > _utcnow():
        raise AccountLockedError(professional.locked_until)

    if not verify_password(password, professional.password_hash):
        professional.failed_login_attempts += 1
        if professional.failed_login_attempts >= settings.professional_max_failed_logins:
            professional.locked_until = _utcnow() + timedelta(minutes=settings.professional_lockout_minutes)
            professional.failed_login_attempts = 0
        db.commit()
        raise InvalidCredentialsError()

    professional.failed_login_attempts = 0
    professional.locked_until = None
    db.commit()

    purpose = PRE_AUTH_PURPOSE_MFA_VERIFY if professional.mfa_enabled else PRE_AUTH_PURPOSE_MFA_SETUP
    token = create_pre_auth_token(professional.id, purpose)
    return LoginChallenge(professional_id=professional.id, pre_auth_token=token, purpose=purpose)


def start_mfa_setup(db: Session, pre_auth_token: str) -> tuple[Professional, str]:
    """Gera e persiste um novo segredo TOTP (pendente até `confirm_mfa_setup`). Retorna
    (professional, provisioning_uri) para o frontend renderizar o QR Code."""
    try:
        professional_id = decode_pre_auth_token(pre_auth_token, PRE_AUTH_PURPOSE_MFA_SETUP)
    except Exception as exc:
        raise InvalidCredentialsError() from exc

    professional = db.get(Professional, professional_id)
    if professional is None:
        raise InvalidCredentialsError()

    secret = generate_totp_secret()
    professional.mfa_secret = secret
    db.commit()
    db.refresh(professional)
    return professional, totp_provisioning_uri(secret, professional.email)


def confirm_mfa_setup(db: Session, pre_auth_token: str, code: str) -> Professional:
    try:
        professional_id = decode_pre_auth_token(pre_auth_token, PRE_AUTH_PURPOSE_MFA_SETUP)
    except Exception as exc:
        raise InvalidCredentialsError() from exc

    professional = db.get(Professional, professional_id)
    if professional is None or professional.mfa_secret is None:
        raise InvalidCredentialsError()
    if not verify_totp_code(professional.mfa_secret, code):
        raise InvalidMfaCodeError()

    professional.mfa_enabled = True
    db.commit()
    db.refresh(professional)
    return professional


def verify_mfa(db: Session, pre_auth_token: str, code: str) -> Professional:
    try:
        professional_id = decode_pre_auth_token(pre_auth_token, PRE_AUTH_PURPOSE_MFA_VERIFY)
    except Exception as exc:
        raise InvalidCredentialsError() from exc

    professional = db.get(Professional, professional_id)
    if professional is None or not professional.mfa_enabled or professional.mfa_secret is None:
        raise InvalidCredentialsError()
    if not verify_totp_code(professional.mfa_secret, code):
        raise InvalidMfaCodeError()
    return professional


def create_session(
    db: Session, professional: Professional, *, ip_address: str | None = None, user_agent: str | None = None
) -> str:
    """Cria a sessão e retorna o token bruto (só existe em memória; o banco guarda o hash)."""
    settings = get_settings()
    raw_token = generate_opaque_token()
    session = ProfessionalSession(
        professional_id=professional.id,
        session_token_hash=hash_opaque_token(raw_token),
        expires_at=_utcnow() + timedelta(minutes=settings.professional_session_expire_minutes),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    return raw_token


def get_professional_from_session_token(db: Session, raw_token: str | None) -> Professional | None:
    if not raw_token:
        return None
    session = (
        db.query(ProfessionalSession)
        .filter(ProfessionalSession.session_token_hash == hash_opaque_token(raw_token))
        .first()
    )
    if session is None or session.revoked_at is not None or session.expires_at < _utcnow():
        return None
    session.last_seen_at = _utcnow()
    db.commit()
    return db.get(Professional, session.professional_id)


def revoke_session(db: Session, raw_token: str) -> None:
    session = (
        db.query(ProfessionalSession)
        .filter(ProfessionalSession.session_token_hash == hash_opaque_token(raw_token))
        .first()
    )
    if session is not None:
        session.revoked_at = _utcnow()
        db.commit()


def revoke_all_sessions(db: Session, professional_id: int) -> None:
    db.query(ProfessionalSession).filter(
        ProfessionalSession.professional_id == professional_id, ProfessionalSession.revoked_at.is_(None)
    ).update({"revoked_at": _utcnow()})
    db.commit()


def request_password_reset(db: Session, email: str) -> str | None:
    """Retorna o token bruto quando o e-mail existe, ou None (o chamador nunca revela qual
    dos dois foi, só registra o link/token no log — não há provedor de e-mail configurado)."""
    settings = get_settings()
    professional = db.query(Professional).filter(Professional.email == email).first()
    if professional is None:
        return None

    raw_token = generate_opaque_token()
    reset = ProfessionalPasswordResetToken(
        professional_id=professional.id,
        token_hash=hash_opaque_token(raw_token),
        expires_at=_utcnow() + timedelta(minutes=settings.professional_password_reset_expire_minutes),
    )
    db.add(reset)
    db.commit()
    return raw_token


def confirm_password_reset(db: Session, raw_token: str, new_password: str) -> Professional:
    reset = (
        db.query(ProfessionalPasswordResetToken)
        .filter(ProfessionalPasswordResetToken.token_hash == hash_opaque_token(raw_token))
        .first()
    )
    if reset is None or reset.consumed_at is not None or reset.expires_at < _utcnow():
        raise InvalidOrExpiredTokenError()

    professional = db.get(Professional, reset.professional_id)
    professional.password_hash = hash_password(new_password)
    professional.failed_login_attempts = 0
    professional.locked_until = None
    reset.consumed_at = _utcnow()
    db.commit()
    revoke_all_sessions(db, professional.id)
    return professional


class InvalidVerificationStatusError(ProfessionalAuthError):
    pass


def list_professionals(db: Session, verification_status: str | None = None) -> list[Professional]:
    """Seção 3: "Verificar solicitações de acesso" — listagem usada pelo administrador."""
    query = db.query(Professional)
    if verification_status is not None:
        query = query.filter(Professional.verification_status == verification_status)
    return query.order_by(Professional.created_at.desc()).all()


def set_verification_status(db: Session, professional: Professional, new_status: str) -> Professional:
    if new_status not in ("verified", "rejected", "pending"):
        raise InvalidVerificationStatusError()
    professional.verification_status = new_status
    db.commit()
    db.refresh(professional)
    return professional
