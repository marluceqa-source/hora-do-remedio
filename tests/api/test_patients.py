"""Fluxo HTTP de cadastro de pacientes e convite de vínculo com o Telegram (RF03, RF04)."""

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


def test_create_and_list_patient(client):
    _signup_and_login(client, "medica.pacientes@example.com")

    create_response = client.post(
        "/api/v1/patients", json={"full_name": "Paciente Um", "internal_identifier": "API-PAC-001"}
    )
    assert create_response.status_code == 201
    patient_id = create_response.json()["id"]
    assert create_response.json()["telegram_link_status"] == "not_linked"

    list_response = client.get("/api/v1/patients")
    assert list_response.status_code == 200
    assert any(p["id"] == patient_id for p in list_response.json())


def test_duplicate_internal_identifier_returns_409(client):
    _signup_and_login(client, "duplicado.paciente@example.com")
    client.post("/api/v1/patients", json={"full_name": "A", "internal_identifier": "API-PAC-DUP"})
    response = client.post("/api/v1/patients", json={"full_name": "B", "internal_identifier": "API-PAC-DUP"})
    assert response.status_code == 409


def test_admin_cannot_create_patient_but_can_list(client):
    _signup_and_login(client, "admin.pacientes@example.com", role="admin", profession="Administrador")
    response = client.post(
        "/api/v1/patients", json={"full_name": "Paciente", "internal_identifier": "API-PAC-ADMIN"}
    )
    assert response.status_code == 403

    list_response = client.get("/api/v1/patients")
    assert list_response.status_code == 200


def test_rn22_other_professional_cannot_see_patient(client):
    _signup_and_login(client, "dono.paciente@example.com")
    created = client.post(
        "/api/v1/patients", json={"full_name": "Paciente Privado", "internal_identifier": "API-PAC-PRIV"}
    )
    patient_id = created.json()["id"]

    _signup_and_login(client, "estranho.paciente@example.com")
    response = client.get(f"/api/v1/patients/{patient_id}")
    assert response.status_code == 404


def test_create_invite_returns_token_and_updates_status(client):
    _signup_and_login(client, "convite.medica@example.com")
    created = client.post(
        "/api/v1/patients", json={"full_name": "Paciente Convite", "internal_identifier": "API-PAC-INVITE"}
    )
    patient_id = created.json()["id"]

    invite_response = client.post(f"/api/v1/patients/{patient_id}/invites")
    assert invite_response.status_code == 201
    body = invite_response.json()
    assert body["token"]
    assert body["expires_at"]

    patient_response = client.get(f"/api/v1/patients/{patient_id}")
    assert patient_response.json()["telegram_link_status"] == "invited"


def test_cannot_create_invite_for_already_linked_patient(client, db_session):
    _signup_and_login(client, "ja.vinculado@example.com")
    created = client.post(
        "/api/v1/patients", json={"full_name": "Paciente Vinculado", "internal_identifier": "API-PAC-LINKED"}
    )
    patient_id = created.json()["id"]
    client.post(f"/api/v1/patients/{patient_id}/invites")

    from database.models import Patient

    patient = db_session.get(Patient, patient_id)
    patient.telegram_link_status = "linked"
    db_session.commit()

    response = client.post(f"/api/v1/patients/{patient_id}/invites")
    assert response.status_code == 409
