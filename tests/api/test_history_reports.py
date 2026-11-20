from datetime import date, datetime

from database.models import Medication, ReminderEvent, User
from tests.api.conftest import headers_for


def _seed_reminder(db_session, telegram_user_id: int, status: str = "pending") -> ReminderEvent:
    user = User(telegram_user_id=telegram_user_id, timezone="America/Sao_Paulo")
    db_session.add(user)
    db_session.flush()

    medication = Medication(
        user_id=user.id,
        name="Medicamento C",
        dosage="20mg",
        quantity="1 cápsula",
        start_date=date.today(),
    )
    db_session.add(medication)
    db_session.flush()

    reminder = ReminderEvent(
        medication_id=medication.id,
        scheduled_datetime=datetime.now(),  # naive, horário local do usuário (ver convenção em database/models.py)
        status=status,
    )
    db_session.add(reminder)
    db_session.commit()
    db_session.refresh(reminder)
    return reminder


def test_history_filtra_por_dia(client, db_session):
    reminder = _seed_reminder(db_session, telegram_user_id=620)
    headers = headers_for(client, 620)

    response = client.get("/api/v1/history", params={"period": "day"}, headers=headers)
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert reminder.id in ids


def test_ct16_geracao_de_relatorio(client, db_session):
    _seed_reminder(db_session, telegram_user_id=630, status="confirmed")
    headers = headers_for(client, 630)

    json_response = client.get("/api/v1/reports", headers=headers)
    assert json_response.status_code == 200
    body = json_response.json()
    assert body["total_confirmed"] == 1
    assert body["confirmation_rate"] == 100.0

    csv_response = client.get("/api/v1/reports", params={"format": "csv"}, headers=headers)
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert "total_confirmed" in csv_response.text
