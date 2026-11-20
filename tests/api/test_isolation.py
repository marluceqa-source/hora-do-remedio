"""RN09: cada usuário acessa apenas seus próprios dados — cobertura ampla (CT41)."""

from tests.api.conftest import headers_for

_MEDICATION_PAYLOAD = {
    "name": "Hidroclorotiazida",
    "dosage": "25mg",
    "quantity": "1 comprimido",
    "start_date": "2026-01-01",
    "schedules": [{"recurrence_type": "daily", "schedule_time": "07:00:00"}],
}


def test_ct41_schedules_are_isolated_between_users(client, auth_headers):
    client.post("/api/v1/medications", json=_MEDICATION_PAYLOAD, headers=auth_headers)

    other_headers = headers_for(client, 810001)
    response = client.get("/api/v1/schedules", headers=other_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_ct41_history_is_isolated_between_users(client, db_session):
    from datetime import date, datetime

    from database.models import Medication, ReminderEvent, User

    owner = User(telegram_user_id=810002, timezone="America/Sao_Paulo")
    db_session.add(owner)
    db_session.flush()
    medication = Medication(
        user_id=owner.id, name="Furosemida", dosage="40mg", quantity="1 comprimido", start_date=date.today()
    )
    db_session.add(medication)
    db_session.flush()
    db_session.add(ReminderEvent(medication_id=medication.id, scheduled_datetime=datetime.now(), status="pending"))
    db_session.commit()

    other_headers = headers_for(client, 810003)
    response = client.get("/api/v1/history", headers=other_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_ct41_reports_are_isolated_between_users(client, auth_headers):
    client.post("/api/v1/medications", json=_MEDICATION_PAYLOAD, headers=auth_headers)

    other_headers = headers_for(client, 810004)
    response = client.get("/api/v1/reports", headers=other_headers)
    assert response.status_code == 200
    assert response.json()["total_scheduled"] == 0


def test_ct41_medications_list_is_isolated_between_users(client, auth_headers):
    client.post("/api/v1/medications", json=_MEDICATION_PAYLOAD, headers=auth_headers)

    other_headers = headers_for(client, 810005)
    response = client.get("/api/v1/medications", headers=other_headers)
    assert response.status_code == 200
    assert response.json() == []
