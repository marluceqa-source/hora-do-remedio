"""Fluxo HTTP de cadastro, ativação e suspensão de tratamentos (RF05-RF07)."""

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


def _medication_payload(**overrides) -> dict:
    payload = {
        "medication_name": "Losartana",
        "dosage": "50mg",
        "quantity_per_administration": "1 comprimido",
        "start_date": "2026-01-01",
        "schedules": [{"recurrence_type": "daily", "schedule_time": "08:00:00"}],
    }
    payload.update(overrides)
    return payload


def _create_patient(client, identifier: str) -> int:
    response = client.post("/api/v1/patients", json={"full_name": "Paciente", "internal_identifier": identifier})
    return response.json()["id"]


def test_create_treatment_medication_is_draft(client):
    _signup_and_login(client, "trt.medica@example.com")
    patient_id = _create_patient(client, "API-TRT-001")

    response = client.post(f"/api/v1/patients/{patient_id}/medications", json=_medication_payload())
    assert response.status_code == 201
    assert response.json()["status"] == "draft"
    assert response.json()["linked_medication_id"] is None


def test_activate_requires_linked_patient(client):
    _signup_and_login(client, "trt.naovinculado@example.com")
    patient_id = _create_patient(client, "API-TRT-002")
    treatment = client.post(f"/api/v1/patients/{patient_id}/medications", json=_medication_payload()).json()

    response = client.post(f"/api/v1/treatment-medications/{treatment['id']}/activate")
    assert response.status_code == 409


def test_enfermeiro_cannot_activate(client, db_session):
    _signup_and_login(client, "trt.enfermeira@example.com", role="enfermeiro", profession="Enfermeiro")
    patient_id = _create_patient(client, "API-TRT-003")
    treatment = client.post(f"/api/v1/patients/{patient_id}/medications", json=_medication_payload()).json()

    from database.models import Patient

    patient = db_session.get(Patient, patient_id)
    from services.medication_service import get_or_create_user

    user = get_or_create_user(db_session, 920001)
    patient.user_id = user.id
    patient.telegram_link_status = "linked"
    db_session.commit()

    response = client.post(f"/api/v1/treatment-medications/{treatment['id']}/activate")
    assert response.status_code == 403


def test_full_activation_flow_notifies_and_materializes(client, db_session):
    from unittest.mock import patch

    _signup_and_login(client, "trt.ativacao@example.com")
    patient_id = _create_patient(client, "API-TRT-004")
    treatment = client.post(f"/api/v1/patients/{patient_id}/medications", json=_medication_payload()).json()

    from database.models import Patient
    from services.medication_service import get_or_create_user

    patient = db_session.get(Patient, patient_id)
    user = get_or_create_user(db_session, 920002)
    patient.user_id = user.id
    patient.telegram_link_status = "linked"
    db_session.commit()

    with patch("api.routes.treatment_medications.send_medication_registered_notification") as mocked_notify:
        response = client.post(f"/api/v1/treatment-medications/{treatment['id']}/activate")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "active"
        assert body["linked_medication_id"] is not None
        mocked_notify.assert_called_once_with(body["linked_medication_id"])


def test_suspend_requires_active_status(client):
    _signup_and_login(client, "trt.suspende@example.com")
    patient_id = _create_patient(client, "API-TRT-005")
    treatment = client.post(f"/api/v1/patients/{patient_id}/medications", json=_medication_payload()).json()

    response = client.post(f"/api/v1/treatment-medications/{treatment['id']}/suspend")
    assert response.status_code == 409


def test_update_draft_then_versions_endpoint(client):
    _signup_and_login(client, "trt.versoes@example.com")
    patient_id = _create_patient(client, "API-TRT-006")
    treatment = client.post(f"/api/v1/patients/{patient_id}/medications", json=_medication_payload()).json()

    patch_response = client.patch(f"/api/v1/treatment-medications/{treatment['id']}", json={"dosage": "100mg"})
    assert patch_response.status_code == 200
    assert patch_response.json()["id"] == treatment["id"]
    assert patch_response.json()["dosage"] == "100mg"

    versions_response = client.get(f"/api/v1/treatment-medications/{treatment['id']}/versions")
    assert versions_response.status_code == 200
    assert len(versions_response.json()) == 1


def test_rn22_other_professional_cannot_act_on_treatment(client):
    _signup_and_login(client, "trt.dono@example.com")
    patient_id = _create_patient(client, "API-TRT-007")
    treatment = client.post(f"/api/v1/patients/{patient_id}/medications", json=_medication_payload()).json()

    _signup_and_login(client, "trt.estranho@example.com")
    response = client.patch(f"/api/v1/treatment-medications/{treatment['id']}", json={"dosage": "999mg"})
    assert response.status_code == 404
