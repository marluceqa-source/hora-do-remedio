from tests.api.conftest import headers_for


def _medication_payload(**overrides):
    payload = {
        "name": "Medicamento A",
        "dosage": "500mg",
        "quantity": "1 comprimido",
        "start_date": "2026-01-01",
        "schedules": [{"recurrence_type": "daily", "schedule_time": "08:00:00"}],
    }
    payload.update(overrides)
    return payload


def test_ct01_cadastro_valido_de_medicamento(client, auth_headers):
    response = client.post("/api/v1/medications", json=_medication_payload(), headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Medicamento A"
    assert len(body["schedules"]) == 1
    assert body["active"] is True


def test_ct02_cadastro_com_nome_vazio(client, auth_headers):
    response = client.post("/api/v1/medications", json=_medication_payload(name=""), headers=auth_headers)
    assert response.status_code == 422


def test_ct03_cadastro_com_horario_invalido(client, auth_headers):
    payload = _medication_payload(schedules=[{"recurrence_type": "daily"}])  # falta schedule_time
    response = client.post("/api/v1/medications", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_ct04_cadastro_com_multiplos_horarios(client, auth_headers):
    payload = _medication_payload(
        schedules=[
            {"recurrence_type": "daily", "schedule_time": "08:00:00"},
            {"recurrence_type": "daily", "schedule_time": "20:00:00"},
        ]
    )
    response = client.post("/api/v1/medications", json=payload, headers=auth_headers)
    assert response.status_code == 201
    assert len(response.json()["schedules"]) == 2


def test_ct09_exclusao_de_medicamento_exige_confirmacao(client, auth_headers):
    created = client.post("/api/v1/medications", json=_medication_payload(), headers=auth_headers).json()
    medication_id = created["id"]

    denied = client.delete(f"/api/v1/medications/{medication_id}", headers=auth_headers)
    assert denied.status_code == 400

    confirmed = client.delete(f"/api/v1/medications/{medication_id}?confirm=true", headers=auth_headers)
    assert confirmed.status_code == 204


def test_ct10_atualizacao_de_horario(client, auth_headers):
    created = client.post("/api/v1/medications", json=_medication_payload(), headers=auth_headers).json()
    medication_id = created["id"]

    response = client.patch(
        f"/api/v1/medications/{medication_id}",
        json={"schedules": [{"recurrence_type": "daily", "schedule_time": "12:30:00"}]},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["schedules"]) == 1
    assert body["schedules"][0]["schedule_time"] == "12:30:00"


def test_ct12_tentativa_de_acesso_por_outro_usuario(client, auth_headers):
    created = client.post("/api/v1/medications", json=_medication_payload(), headers=auth_headers).json()
    medication_id = created["id"]

    other_headers = headers_for(client, 999999999)
    response = client.get(f"/api/v1/medications/{medication_id}", headers=other_headers)
    assert response.status_code == 404


def test_api_requires_authentication(client):
    response = client.get("/api/v1/medications")
    assert response.status_code == 401
