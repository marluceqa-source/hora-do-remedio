from datetime import date, datetime

from database.models import Medication, ReminderEvent, User
from tests.api.conftest import headers_for


def _seed_reminder(db_session, telegram_user_id: int, status: str = "pending") -> ReminderEvent:
    user = User(telegram_user_id=telegram_user_id, timezone="America/Sao_Paulo")
    db_session.add(user)
    db_session.flush()

    medication = Medication(
        user_id=user.id,
        name="Medicamento B",
        dosage="10mg",
        quantity="1 comprimido",
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


def test_ct05_reminders_today_lista_lembretes_do_dia(client, db_session):
    reminder = _seed_reminder(db_session, telegram_user_id=601)
    headers = headers_for(client, 601)

    response = client.get("/api/v1/reminders/today", headers=headers)
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert reminder.id in ids


def test_ct06_confirmacao_de_administracao(client, db_session):
    reminder = _seed_reminder(db_session, telegram_user_id=606)
    headers = headers_for(client, 606)

    response = client.post(f"/api/v1/reminders/{reminder.id}/confirm", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
    assert response.json()["confirmed_datetime"] is not None


def test_ct07_confirmacao_duplicada(client, db_session):
    reminder = _seed_reminder(db_session, telegram_user_id=607)
    headers = headers_for(client, 607)

    first = client.post(f"/api/v1/reminders/{reminder.id}/confirm", headers=headers)
    assert first.status_code == 200

    second = client.post(f"/api/v1/reminders/{reminder.id}/confirm", headers=headers)
    assert second.status_code == 409


def test_ct08_adiamento_nao_altera_horario_original(client, db_session):
    reminder = _seed_reminder(db_session, telegram_user_id=608)
    headers = headers_for(client, 608)
    original_scheduled = reminder.scheduled_datetime.isoformat()

    response = client.post(f"/api/v1/reminders/{reminder.id}/snooze", json={"minutes": 10}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "snoozed"
    assert body["snooze_count"] == 1
    assert body["scheduled_datetime"] == original_scheduled


def test_reminder_access_denied_to_other_user(client, db_session):
    reminder = _seed_reminder(db_session, telegram_user_id=612)
    other_headers = headers_for(client, 613)

    response = client.post(f"/api/v1/reminders/{reminder.id}/confirm", headers=other_headers)
    assert response.status_code == 404
