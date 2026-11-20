import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.professional import (
    LoginChallengeOut,
    LoginRequest,
    MfaCodeRequest,
    MfaSetupStartResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PreAuthTokenRequest,
    ProfessionalOut,
    ProfessionalSignupRequest,
)
from core.config import get_settings
from core.professional_security import get_current_professional
from database.models import Professional
from services import professional_auth_service as auth_service
from services.audit_service import log_audit

router = APIRouter(prefix="/api/v1", tags=["Portal — Autenticação"])

logger = logging.getLogger(__name__)


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.professional_session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.professional_session_expire_minutes * 60,
        path="/",
    )


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post(
    "/professionals",
    response_model=ProfessionalOut,
    status_code=status.HTTP_201_CREATED,
    summary="Solicita cadastro de profissional (RF01) — não concede permissões clínicas automaticamente",
)
def signup_professional(payload: ProfessionalSignupRequest, db: Session = Depends(get_db)) -> Professional:
    try:
        professional = auth_service.register_professional(
            db,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            profession=payload.profession,
            council_type=payload.council_type,
            council_number=payload.council_number,
            council_state=payload.council_state,
            institution=payload.institution,
        )
    except auth_service.EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado") from exc

    log_audit(db, professional.id, professional.role, "professional.signup_requested", "professional", professional.id)
    return professional


@router.get(
    "/professionals/me",
    response_model=ProfessionalOut,
    summary="Consulta o perfil do profissional autenticado",
)
def get_my_profile(professional: Professional = Depends(get_current_professional)) -> Professional:
    return professional


@router.post(
    "/auth/professional/login",
    response_model=LoginChallengeOut,
    summary="1ª etapa do login: valida e-mail/senha e devolve o desafio de MFA (RF01)",
)
def login_step1(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> LoginChallengeOut:
    try:
        challenge = auth_service.authenticate_password(db, payload.email, payload.password)
    except auth_service.AccountLockedError as exc:
        log_audit(db, None, "unknown", "auth.login_blocked_locked", "professional")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Conta temporariamente bloqueada por tentativas indevidas. Tente novamente após {exc.locked_until.isoformat()}Z.",
        ) from exc
    except auth_service.InvalidCredentialsError as exc:
        log_audit(db, None, "unknown", "auth.login_failed", "professional")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos") from exc

    log_audit(db, challenge.professional_id, "unknown", "auth.password_verified", "professional", challenge.professional_id)
    return LoginChallengeOut(pre_auth_token=challenge.pre_auth_token, purpose=challenge.purpose)


@router.post(
    "/auth/professional/mfa/setup",
    response_model=MfaSetupStartResponse,
    summary="Inicia a configuração do MFA (1º login) — renderize provisioning_uri como QR Code",
)
def start_mfa_setup(payload: PreAuthTokenRequest, db: Session = Depends(get_db)) -> MfaSetupStartResponse:
    try:
        _professional, provisioning_uri = auth_service.start_mfa_setup(db, payload.pre_auth_token)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de pré-autenticação inválido") from exc

    return MfaSetupStartResponse(provisioning_uri=provisioning_uri, pre_auth_token=payload.pre_auth_token)


@router.post(
    "/auth/professional/mfa/confirm",
    response_model=ProfessionalOut,
    summary="Confirma o código TOTP e ativa o MFA, iniciando a sessão (RF01)",
)
def confirm_mfa_setup(
    payload: MfaCodeRequest, request: Request, response: Response, db: Session = Depends(get_db)
) -> Professional:
    try:
        professional = auth_service.confirm_mfa_setup(db, payload.pre_auth_token, payload.code)
    except auth_service.InvalidMfaCodeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Código de verificação inválido") from exc
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de pré-autenticação inválido") from exc

    token = auth_service.create_session(
        db, professional, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent")
    )
    _set_session_cookie(response, token)
    log_audit(db, professional.id, professional.role, "auth.mfa_setup_confirmed", "professional", professional.id)
    log_audit(db, professional.id, professional.role, "auth.login_success", "professional", professional.id)
    return professional


@router.post(
    "/auth/professional/mfa/verify",
    response_model=ProfessionalOut,
    summary="2ª etapa do login (profissionais com MFA já ativo): envia o código e recebe a sessão",
)
def verify_mfa(payload: MfaCodeRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> Professional:
    try:
        professional = auth_service.verify_mfa(db, payload.pre_auth_token, payload.code)
    except auth_service.InvalidMfaCodeError as exc:
        log_audit(db, None, "unknown", "auth.mfa_verify_failed", "professional")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Código de verificação inválido") from exc
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de pré-autenticação inválido") from exc

    token = auth_service.create_session(
        db, professional, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent")
    )
    _set_session_cookie(response, token)
    log_audit(db, professional.id, professional.role, "auth.login_success", "professional", professional.id)
    return professional


@router.post(
    "/auth/professional/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Encerra a sessão atual (RF01)",
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    professional: Professional = Depends(get_current_professional),
) -> None:
    settings = get_settings()
    token = request.cookies.get(settings.professional_session_cookie_name)
    if token:
        auth_service.revoke_session(db, token)
    response.delete_cookie(settings.professional_session_cookie_name, path="/")
    log_audit(db, professional.id, professional.role, "auth.logout", "professional", professional.id)


@router.post(
    "/auth/professional/password-reset/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicita recuperação de acesso (RF01) — não revela se o e-mail existe",
)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> dict:
    token = auth_service.request_password_reset(db, payload.email)
    if token is not None:
        # Sem provedor de e-mail configurado neste ambiente: o link fica só no log do servidor.
        logger.info(
            "Token de recuperação de acesso gerado para %s: %s (válido por %s min)",
            payload.email,
            token,
            get_settings().professional_password_reset_expire_minutes,
        )
        log_audit(db, None, "unknown", "auth.password_reset_requested", "professional")
    return {"detail": "Se o e-mail existir, instruções de recuperação foram geradas."}


@router.post(
    "/auth/professional/password-reset/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Confirma a nova senha a partir do token de recuperação (RF01)",
)
def confirm_password_reset(payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)) -> None:
    try:
        professional = auth_service.confirm_password_reset(db, payload.token, payload.new_password)
    except auth_service.InvalidOrExpiredTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido ou expirado") from exc

    log_audit(db, professional.id, professional.role, "auth.password_reset_confirmed", "professional", professional.id)
