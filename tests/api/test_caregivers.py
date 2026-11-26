from tests.api.conftest import headers_for


def test_grant_and_list_caregiver_access(client, auth_headers):
    response = client.post(
        "/api/v1/caregivers", json={"caregiver_telegram_user_id": 700001, "permission": "view"}, headers=auth_headers
    )
    assert response.status_code == 201
    access_id = response.json()["id"]

    listing = client.get("/api/v1/caregivers", headers=auth_headers)
    assert listing.status_code == 200
    assert any(item["id"] == access_id for item in listing.json())


def test_revoke_caregiver_access(client, auth_headers):
    created = client.post(
        "/api/v1/caregivers", json={"caregiver_telegram_user_id": 700002}, headers=auth_headers
    ).json()

    revoke = client.delete(f"/api/v1/caregivers/{created['id']}", headers=auth_headers)
    assert revoke.status_code == 204

    listing = client.get("/api/v1/caregivers", headers=auth_headers).json()
    assert all(item["id"] != created["id"] for item in listing)


def test_cannot_revoke_someone_elses_caregiver_access(client, auth_headers):
    created = client.post(
        "/api/v1/caregivers", json={"caregiver_telegram_user_id": 700003}, headers=auth_headers
    ).json()

    other_headers = headers_for(client, 700004)
    response = client.delete(f"/api/v1/caregivers/{created['id']}", headers=other_headers)
    assert response.status_code == 404


def test_ct28_caregiver_can_view_authorized_patient_medications(client, auth_headers):
    """CT28 — acesso autorizado de cuidador, do convite à leitura dos medicamentos."""
    patient_info = client.get("/api/v1/medications", headers=auth_headers)
    assert patient_info.status_code == 200

    client.post(
        "/api/v1/medications",
        json={
            "name": "Sinvastatina",
            "dosage": "20mg",
            "quantity": "1 comprimido",
            "start_date": "2026-01-01",
            "schedules": [{"recurrence_type": "daily", "schedule_time": "22:00:00"}],
        },
        headers=auth_headers,
    )

    grant = client.post(
        "/api/v1/caregivers", json={"caregiver_telegram_user_id": 700005}, headers=auth_headers
    ).json()
    patient_user_id = grant["user_id"]

    caregiver_headers = headers_for(client, 700005)
    response = client.get(f"/api/v1/caregivers/patients/{patient_user_id}/medications", headers=caregiver_headers)
    assert response.status_code == 200
    assert any(m["name"] == "Sinvastatina" for m in response.json())


def test_unauthorized_caregiver_cannot_view_patient_medications(client, auth_headers):
    grant = client.post(
        "/api/v1/caregivers", json={"caregiver_telegram_user_id": 700006}, headers=auth_headers
    ).json()
    patient_user_id = grant["user_id"]

    stranger_headers = headers_for(client, 700007)
    response = client.get(f"/api/v1/caregivers/patients/{patient_user_id}/medications", headers=stranger_headers)
    assert response.status_code == 403
