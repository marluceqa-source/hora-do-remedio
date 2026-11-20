"""RF02 (dashboard), RF08 (histórico do paciente) e seção 3 (admin: auditoria/verificação)."""

from urllib.parse import parse_qs, urlparse

import pyotp


def _extract_secret(provisioning_uri: str) -> str:
    return parse_qs(urlparse(provisioning_uri).query)["secret"][0]


def _signup_and_login(client, email: str, role: str = "medico", profession: str = "Médico") -> None:
    client.post(
        "/api/v1/professionals",
        json={
            "full_name": "Profissional Teste",
            "email": email,
            "password": "SenhaForte123",
            "role": role,
            "profession": profession,
        },
    )
    login = client.post("/api/v1/auth/professional/login", json={"email": email, "password": "SenhaForte123"})
    challenge = login.json()
    setup = client.post("/api/v1/auth/professional/mfa/setup", json={"pre_auth_token": challenge["pre_auth_token"]})
    secret = _extract_secret(setup.json()["provisioning_uri"])
    code = pyotp.TOTP(secret).now()
    confirm = client.post(
        "/api/v1/auth/professional/mfa/confirm", json={"pre_auth_token": challenge["pre_auth_token"], "code": code}
    )
    assert confirm.status_code == 200


def test_dashboard_reflects_created_patient(client):
    _signup_and_login(client, "dash.api@example.com")
    client.post("/api/v1/patients", json={"full_name": "Paciente", "internal_identifier": "DASH-API-001"})

    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    assert response.json()["total_patients"] == 1
    assert response.json()["active_treatments"] == 0


def test_patient_history_empty_when_not_linked(client):
    _signup_and_login(client, "hist.naovinculado@example.com")
    created = client.post(
        "/api/v1/patients", json={"full_name": "Paciente", "internal_identifier": "HIST-API-001"}
    ).json()

    response = client.get(f"/api/v1/patients/{created['id']}/history")
    assert response.status_code == 200
    assert response.json() == []


def test_non_admin_cannot_access_admin_endpoints(client):
    _signup_and_login(client, "naoadmin@example.com")
    assert client.get("/api/v1/audit-logs").status_code == 403
    assert client.get("/api/v1/professionals").status_code == 403
    assert client.post("/api/v1/professionals/1/verify", json={"verification_status": "verified"}).status_code == 403


def test_admin_can_verify_professional_and_read_audit_logs(client, db_session):
    _signup_and_login(client, "pendente@example.com")  # gera um audit log "signup_requested"

    from database.models import Professional

    pending = db_session.query(Professional).filter(Professional.email == "pendente@example.com").one()
    assert pending.verification_status == "pending"

    _signup_and_login(client, "admin.verify@example.com", role="admin", profession="Administrador")

    verify_response = client.post(
        f"/api/v1/professionals/{pending.id}/verify", json={"verification_status": "verified"}
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["verification_status"] == "verified"

    audit_response = client.get("/api/v1/audit-logs", params={"resource_type": "professional"})
    assert audit_response.status_code == 200
    actions = [entry["action"] for entry in audit_response.json()]
    assert "professional.verification_verified" in actions


def test_admin_list_professionals_filter_by_status(client):
    _signup_and_login(client, "filtro.pendente@example.com")
    _signup_and_login(client, "filtro.admin@example.com", role="admin", profession="Administrador")

    response = client.get("/api/v1/professionals", params={"verification_status": "pending"})
    assert response.status_code == 200
    emails = [p["email"] for p in response.json()]
    # Cadastro nunca concede verificação automática (RF01) — mesmo o admin recém-criado
    # aparece como "pending" até outro admin verificá-lo.
    assert "filtro.pendente@example.com" in emails
    assert "filtro.admin@example.com" in emails

    verified_response = client.get("/api/v1/professionals", params={"verification_status": "verified"})
    assert verified_response.json() == []
