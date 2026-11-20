from datetime import date, datetime

from database.models import Medication, ReminderEvent, User
from services.report_service import compute_report


def _seed_user_with_events(db_session, statuses: list[str]) -> User:
    user = User(telegram_user_id=200, timezone="America/Sao_Paulo")
    db_session.add(user)
    db_session.flush()

    medication = Medication(
        user_id=user.id, name="Omeprazol", dosage="20mg", quantity="1 cápsula", start_date=date.today()
    )
    db_session.add(medication)
    db_session.flush()

    for status in statuses:
        db_session.add(ReminderEvent(medication_id=medication.id, scheduled_datetime=datetime.now(), status=status))
    db_session.commit()
    return user


def test_compute_report_with_no_events(db_session):
    user = User(telegram_user_id=201, timezone="America/Sao_Paulo")
    db_session.add(user)
    db_session.commit()

    report = compute_report(db_session, user)
    assert report["total_scheduled"] == 0
    assert report["confirmation_rate"] == 0.0


def test_compute_report_calculates_rate(db_session):
    user = _seed_user_with_events(db_session, ["confirmed", "confirmed", "not_taken", "pending"])
    report = compute_report(db_session, user)

    assert report["total_scheduled"] == 4
    assert report["total_confirmed"] == 2
    assert report["total_not_taken"] == 1
    assert report["total_unconfirmed"] == 1
    assert report["confirmation_rate"] == 50.0
