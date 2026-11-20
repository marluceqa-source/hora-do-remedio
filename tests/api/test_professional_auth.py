"""Fluxo HTTP completo de autenticação de profissionais (RF01): cadastro, login em 2 etapas
(senha + MFA), sessão por cookie, perfil, logout e recuperação de acesso."""

import pyotp

from core.config import get_settings
from database.models import Professional


def _signup_payload(**overrides) -> dict:
    payload = {
        "full_name": "Dra. Ana Paula",
        "email": "ana.paula@example.com",
        "password": "SenhaForte123",
        "role": "medico",
        "profession": "Médico",
        "council_type": "CRM",
        "council_number": "11111",
        "council_state": "SP",
    }
    payload.update(overrides)
    return payload


def test_signup_then_first_login_mfa_setup_issues_session_cookie(client, db_session):
    signup_response = client.post("/api/v1/professionals", json=_signup_payload())
    assert signup_response.status_code == 201
    body = signup_response.json()
    assert body["verification_status"] == "pending"
    assert body["mfa_enabled"] is False

    login_response = client.post(
        "/api/v1/auth/professional/login", json={"email": "ana.paula@example.com", "password": "SenhaForte123"}
    )
    assert login_response.status_code == 200
    challenge = login_response.json()
    assert challenge["purpose"] == "mfa_setup"

    setup_response = client.post(
        "/api/v1/auth/professional/mfa/setup", json={"pre_auth_token": challenge["pre_auth_token"]}
    )
    assert setup_response.status_code == 200
    assert setup_response.json()["provisioning_uri"].startswith("otpauth://")

    professional = db_session.query(Professional).filter(Professional.email == "ana.paula@example.com").one()
    code = pyotp.TOTP(professional.mfa_secret).now()

    confirm_response = client.post(
        "/api/v1/auth/professional/mfa/confirm",
        json={"pre_auth_token": challenge["pre_auth_token"], "code": code},
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["mfa_enabled"] is True
    assert get_settings().professional_session_cookie_name in confirm_response.cookies

    me_response = client.get("/api/v1/professionals/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "ana.paula@example.com"

    logout_response = client.post("/api/v1/auth/professional/logout")
    assert logout_response.status_code == 204

    me_after_logout = client.get("/api/v1/professionals/me")
    assert me_after_logout.status_code == 401


def test_second_login_with_mfa_already_enabled_uses_verify_step(client, db_session):
    client.post("/api/v1/professionals", json=_signup_payload(email="segundo.login@example.com"))
    login = client.post(
        "/api/v1/auth/professional/login", json={"email": "segundo.login@example.com", "password": "SenhaForte123"}
    )
    challenge = login.json()
    client.post("/api/v1/auth/professional/mfa/setup", json={"pre_auth_token": challenge["pre_auth_token"]})

    professional = db_session.query(Professional).filter(Professional.email == "segundo.login@example.com").one()
    code = pyotp.TOTP(professional.mfa_secret).now()
    client.post(
        "/api/v1/auth/professional/mfa/confirm", json={"pre_auth_token": challenge["pre_auth_token"], "code": code}
    )
    client.post("/api/v1/auth/professional/logout")

    second_login = client.post(
        "/api/v1/auth/professional/login", json={"email": "segundo.login@example.com", "password": "SenhaForte123"}
    )
    second_challenge = second_login.json()
    assert second_challenge["purpose"] == "mfa_verify"

    db_session.refresh(professional)
    verify_code = pyotp.TOTP(professional.mfa_secret).now()
    verify_response = client.post(
        "/api/v1/auth/professional/mfa/verify",
        json={"pre_auth_token": second_challenge["pre_auth_token"], "code": verify_code},
    )
    assert verify_response.status_code == 200
    assert get_settings().professional_session_cookie_name in verify_response.cookies


def test_login_with_wrong_password_returns_401(client):
    client.post("/api/v1/professionals", json=_signup_payload(email="senha.errada@example.com"))
    response = client.post(
        "/api/v1/auth/professional/login", json={"email": "senha.errada@example.com", "password": "errada"}
    )
    assert response.status_code == 401


def test_duplicate_signup_email_returns_409(client):
    client.post("/api/v1/professionals", json=_signup_payload(email="duplicado@example.com"))
    response = client.post("/api/v1/professionals", json=_signup_payload(email="duplicado@example.com"))
    assert response.status_code == 409


def test_account_locks_after_too_many_failed_logins(client):
    client.post("/api/v1/professionals", json=_signup_payload(email="bloqueio@example.com"))
    for _ in range(get_settings().professional_max_failed_logins):
        client.post(
            "/api/v1/auth/professional/login", json={"email": "bloqueio@example.com", "password": "errada"}
        )

    response = client.post(
        "/api/v1/auth/professional/login", json={"email": "bloqueio@example.com", "password": "SenhaForte123"}
    )
    assert response.status_code == 423


def test_password_reset_request_persists_a_pending_token(client, db_session):
    client.post("/api/v1/professionals", json=_signup_payload(email="esqueceu@example.com"))

    request_response = client.post(
        "/api/v1/auth/professional/password-reset/request", json={"email": "esqueceu@example.com"}
    )
    assert request_response.status_code == 202

    # Sem provedor de e-mail configurado: o token em claro só existe no log do servidor (ver
    # core/professional_security.py). Aqui conferimos que o pedido foi persistido; o fluxo de
    # confirmação completo (token -> nova senha -> sessões antigas revogadas) está coberto em
    # tests/unit/test_professional_auth_service.py.
    from database.models import ProfessionalPasswordResetToken

    professional = db_session.query(Professional).filter(Professional.email == "esqueceu@example.com").one()
    reset_row = (
        db_session.query(ProfessionalPasswordResetToken)
        .filter(ProfessionalPasswordResetToken.professional_id == professional.id)
        .one()
    )
    assert reset_row.consumed_at is None


def test_access_without_session_cookie_is_rejected(client):
    response = client.get("/api/v1/professionals/me")
    assert response.status_code == 401
