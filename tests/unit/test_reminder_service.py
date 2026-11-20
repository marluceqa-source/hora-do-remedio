from datetime import date, datetime

import pytest

from database.models import Medication, ReminderEvent, User
from services import reminder_service


def _seed(db_session, telegram_user_id: int, status: str = "pending") -> ReminderEvent:
    user = User(telegram_user_id=telegram_user_id, timezone="America/Sao_Paulo")
    db_session.add(user)
    db_session.flush()

    medication = Medication(
        user_id=user.id,
        name="Vitamina D",
        dosage="2000UI",
        quantity="1 cápsula",
        start_date=date.today(),
    )
    db_session.add(medication)
    db_session.flush()

    reminder = ReminderEvent(medication_id=medication.id, scheduled_datetime=datetime.now(), status=status)
    db_session.add(reminder)
    db_session.commit()
    db_session.refresh(reminder)
    return reminder


def test_confirm_sets_status_and_timestamp(db_session):
    reminder = _seed(db_session, 10)
    confirmed = reminder_service.confirm(db_session, reminder)
    assert confirmed.status == "confirmed"
    assert confirmed.confirmed_datetime is not None


def test_confirm_twice_raises(db_session):
    reminder = _seed(db_session, 11)
    reminder_service.confirm(db_session, reminder)
    with pytest.raises(reminder_service.ReminderAlreadyConfirmedError):
        reminder_service.confirm(db_session, reminder)


def test_snooze_increments_count_without_changing_schedule(db_session):
    reminder = _seed(db_session, 12)
    original = reminder.scheduled_datetime
    snoozed = reminder_service.snooze(db_session, reminder)
    assert snoozed.snooze_count == 1
    assert snoozed.scheduled_datetime == original
    assert snoozed.status == "snoozed"


def test_mark_not_taken_after_confirmation_raises(db_session):
    reminder = _seed(db_session, 13)
    reminder_service.confirm(db_session, reminder)
    with pytest.raises(reminder_service.ReminderAlreadyConfirmedError):
        reminder_service.mark_not_taken(db_session, reminder)


def test_get_owned_reminder_denies_other_user(db_session):
    reminder = _seed(db_session, 14)
    other_user = User(telegram_user_id=15, timezone="America/Sao_Paulo")
    db_session.add(other_user)
    db_session.commit()

    assert reminder_service.get_owned_reminder(db_session, reminder.id, other_user) is None


def test_list_today_only_returns_todays_reminders(db_session):
    reminder = _seed(db_session, 16)
    user = reminder.medication.user
    results = reminder_service.list_today(db_session, user)
    assert reminder.id in [r.id for r in results]
