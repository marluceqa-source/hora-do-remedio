"""services/professional_auth_service.py: cadastro, bloqueio, MFA (TOTP) e sessões (RF01)."""

import pyotp
import pytest

from services import professional_auth_service as auth_service

_PASSWORD = "SenhaForte123"


def _signup(db_session, email: str = "doutora@example.com", password: str = _PASSWORD):
    return auth_service.register_professional(
        db_session,
        full_name="Dra. Teste",
        email=email,
        password=password,
        role="medico",
        profession="Médico",
        council_type="CRM",
        council_number="123",
        council_state="SP",
    )


def test_register_professional_creates_pending_unverified_account(db_session):
    professional = _signup(db_session)
    assert professional.verification_status == "pending"
    assert professional.mfa_enabled is False
    assert professional.password_hash != _PASSWORD  # nunca em texto puro


def test_register_duplicate_email_raises(db_session):
    _signup(db_session)
    with pytest.raises(auth_service.EmailAlreadyRegisteredError):
        _signup(db_session)


def test_authenticate_wrong_password_counts_failed_attempt(db_session):
    professional = _signup(db_session)
    with pytest.raises(auth_service.InvalidCredentialsError):
        auth_service.authenticate_password(db_session, professional.email, "senha-errada")
    db_session.refresh(professional)
    assert professional.failed_login_attempts == 1


def test_authenticate_locks_account_after_max_failed_attempts(db_session):
    professional = _signup(db_session)
    for _ in range(5):
        with pytest.raises(auth_service.InvalidCredentialsError):
            auth_service.authenticate_password(db_session, professional.email, "senha-errada")
    db_session.refresh(professional)
    assert professional.locked_until is not None

    with pytest.raises(auth_service.AccountLockedError):
        auth_service.authenticate_password(db_session, professional.email, _PASSWORD)


def test_authenticate_correct_password_without_mfa_requests_setup(db_session):
    professional = _signup(db_session)
    challenge = auth_service.authenticate_password(db_session, professional.email, _PASSWORD)
    assert challenge.purpose == "mfa_setup"


def test_mfa_setup_and_confirm_enables_mfa_and_allows_session_creation(db_session):
    professional = _signup(db_session)
    challenge = auth_service.authenticate_password(db_session, professional.email, _PASSWORD)

    _professional, provisioning_uri = auth_service.start_mfa_setup(db_session, challenge.pre_auth_token)
    assert provisioning_uri.startswith("otpauth://")

    db_session.refresh(professional)
    code = pyotp.TOTP(professional.mfa_secret).now()

    confirmed = auth_service.confirm_mfa_setup(db_session, challenge.pre_auth_token, code)
    assert confirmed.mfa_enabled is True

    token = auth_service.create_session(db_session, confirmed)
    resolved = auth_service.get_professional_from_session_token(db_session, token)
    assert resolved is not None
    assert resolved.id == confirmed.id


def test_mfa_setup_confirm_with_wrong_code_raises(db_session):
    professional = _signup(db_session)
    challenge = auth_service.authenticate_password(db_session, professional.email, _PASSWORD)
    auth_service.start_mfa_setup(db_session, challenge.pre_auth_token)

    with pytest.raises(auth_service.InvalidMfaCodeError):
        auth_service.confirm_mfa_setup(db_session, challenge.pre_auth_token, "000000")


def _enable_mfa(db_session, professional, password: str = _PASSWORD) -> None:
    challenge = auth_service.authenticate_password(db_session, professional.email, password)
    auth_service.start_mfa_setup(db_session, challenge.pre_auth_token)
    db_session.refresh(professional)
    code = pyotp.TOTP(professional.mfa_secret).now()
    auth_service.confirm_mfa_setup(db_session, challenge.pre_auth_token, code)


def test_login_with_mfa_already_enabled_requires_verify_step(db_session):
    professional = _signup(db_session)
    _enable_mfa(db_session, professional)

    second_challenge = auth_service.authenticate_password(db_session, professional.email, _PASSWORD)
    assert second_challenge.purpose == "mfa_verify"

    db_session.refresh(professional)
    verify_code = pyotp.TOTP(professional.mfa_secret).now()
    verified = auth_service.verify_mfa(db_session, second_challenge.pre_auth_token, verify_code)
    assert verified.id == professional.id


def test_verify_mfa_with_wrong_code_raises(db_session):
    professional = _signup(db_session)
    _enable_mfa(db_session, professional)

    second_challenge = auth_service.authenticate_password(db_session, professional.email, _PASSWORD)
    with pytest.raises(auth_service.InvalidMfaCodeError):
        auth_service.verify_mfa(db_session, second_challenge.pre_auth_token, "000000")


def test_revoke_session_invalidates_it(db_session):
    professional = _signup(db_session)
    token = auth_service.create_session(db_session, professional)
    assert auth_service.get_professional_from_session_token(db_session, token) is not None

    auth_service.revoke_session(db_session, token)
    assert auth_service.get_professional_from_session_token(db_session, token) is None


def test_password_reset_flow_invalidates_old_sessions_and_sets_new_password(db_session):
    professional = _signup(db_session)
    old_token = auth_service.create_session(db_session, professional)

    reset_token = auth_service.request_password_reset(db_session, professional.email)
    assert reset_token is not None

    auth_service.confirm_password_reset(db_session, reset_token, "NovaSenhaForte456")

    assert auth_service.get_professional_from_session_token(db_session, old_token) is None
    # a nova senha já funciona na próxima tentativa de login
    assert auth_service.authenticate_password(db_session, professional.email, "NovaSenhaForte456") is not None


def test_password_reset_request_for_unknown_email_returns_none(db_session):
    assert auth_service.request_password_reset(db_session, "ninguem@example.com") is None


def test_password_reset_confirm_with_invalid_token_raises(db_session):
    with pytest.raises(auth_service.InvalidOrExpiredTokenError):
        auth_service.confirm_password_reset(db_session, "token-invalido", "NovaSenha123")
