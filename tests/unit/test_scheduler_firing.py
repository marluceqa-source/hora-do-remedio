"""Testes do disparo de lembretes com relógio controlado (seção 11: CT05, CT11, CT14, CT15, CT18, CT42)."""

from datetime import date, time
from unittest.mock import MagicMock

from freezegun import freeze_time

from database.models import Medication, ReminderEvent, Schedule, User
from services.scheduler_service import SchedulerService


def _seed_medication(
    db_session, *, start_date: date, end_date: date | None = None, active: bool = True, telegram_user_id: int = 900
):
    user = User(telegram_user_id=telegram_user_id, timezone="America/Sao_Paulo")
    db_session.add(user)
    db_session.flush()

    medication = Medication(
        user_id=user.id,
        name="Enalapril",
        dosage="10mg",
        quantity="1 comprimido",
        start_date=start_date,
        end_date=end_date,
        active=active,
    )
    db_session.add(medication)
    db_session.flush()

    schedule = Schedule(
        medication_id=medication.id,
        recurrence_type="daily",
        schedule_time=time(8, 0),
        timezone="America/Sao_Paulo",
    )
    db_session.add(schedule)
    db_session.commit()
    return medication, schedule


def test_ct05_fire_creates_pending_reminder_and_notifies(db_session, session_factory):
    medication, schedule = _seed_medication(db_session, start_date=date(2026, 1, 1))
    notify = MagicMock()
    service = SchedulerService(notify_callback=notify, session_factory=session_factory)

    with freeze_time("2026-03-10 11:00:00"):
        service._fire(medication.id, schedule.id)

    reminder = db_session.query(ReminderEvent).filter(ReminderEvent.medication_id == medication.id).one()
    assert reminder.status == "pending"
    notify.assert_called_once_with(reminder.id)


def test_ct11_reload_jobs_reconstructs_from_db(db_session, session_factory):
    medication1, schedule1 = _seed_medication(db_session, start_date=date(2026, 1, 1), telegram_user_id=901)
    medication2, schedule2 = _seed_medication(db_session, start_date=date(2026, 1, 1), telegram_user_id=902)

    service = SchedulerService(notify_callback=MagicMock(), session_factory=session_factory)
    service.reload_jobs()

    job_ids = {job.id for job in service._scheduler.get_jobs()}
    assert f"schedule-{schedule1.id}" in job_ids
    assert f"schedule-{schedule2.id}" in job_ids


def test_ct11_reload_jobs_ignores_inactive_medications(db_session, session_factory):
    medication, schedule = _seed_medication(db_session, start_date=date(2026, 1, 1), active=False)

    service = SchedulerService(notify_callback=MagicMock(), session_factory=session_factory)
    service.reload_jobs()

    job_ids = {job.id for job in service._scheduler.get_jobs()}
    assert f"schedule-{schedule.id}" not in job_ids


def test_ct14_fire_respects_schedules_own_timezone_not_utc(db_session, session_factory):
    # Em UTC 2026-03-10 01:30: ainda é 2026-03-09 em America/Sao_Paulo (UTC-3),
    # mas já é 2026-03-10 em Pacific/Kiritimati (UTC+14).
    medication, schedule = _seed_medication(db_session, start_date=date(2026, 3, 10))
    schedule.timezone = "Pacific/Kiritimati"
    db_session.commit()

    notify = MagicMock()
    service = SchedulerService(notify_callback=notify, session_factory=session_factory)

    with freeze_time("2026-03-10 01:30:00"):
        service._fire(medication.id, schedule.id)

    # Nessa data o tratamento já começou no fuso do schedule (Kiritimati), embora em UTC/Sao
    # Paulo ainda fosse o dia anterior — confirma que RN07 usa o fuso do schedule, não o do SO.
    assert db_session.query(ReminderEvent).filter(ReminderEvent.medication_id == medication.id).count() == 1
    notify.assert_called_once()


def test_ct15_fire_skips_after_treatment_end_date(db_session, session_factory):
    medication, schedule = _seed_medication(
        db_session, start_date=date(2026, 1, 1), end_date=date(2026, 3, 9)
    )
    notify = MagicMock()
    service = SchedulerService(notify_callback=notify, session_factory=session_factory)

    with freeze_time("2026-03-10 11:00:00"):
        service._fire(medication.id, schedule.id)

    assert db_session.query(ReminderEvent).filter(ReminderEvent.medication_id == medication.id).count() == 0
    notify.assert_not_called()


def test_ct15_fire_skips_before_treatment_start_date(db_session, session_factory):
    medication, schedule = _seed_medication(db_session, start_date=date(2026, 5, 1))
    notify = MagicMock()
    service = SchedulerService(notify_callback=notify, session_factory=session_factory)

    with freeze_time("2026-03-10 11:00:00"):
        service._fire(medication.id, schedule.id)

    assert db_session.query(ReminderEvent).filter(ReminderEvent.medication_id == medication.id).count() == 0
    notify.assert_not_called()


def test_ct18_fire_recovers_from_unexpected_failure(db_session, session_factory):
    medication, schedule = _seed_medication(db_session, start_date=date(2026, 1, 1))
    schedule.timezone = "Not/A_Real_Zone"  # ZoneInfo levantará exceção dentro de _fire
    db_session.commit()

    notify = MagicMock()
    service = SchedulerService(notify_callback=notify, session_factory=session_factory)

    with freeze_time("2026-03-10 11:00:00"):
        service._fire(medication.id, schedule.id)  # não deve propagar exceção (RN18)

    notify.assert_not_called()

    # Corrige o fuso e confirma que o serviço continua operando normalmente depois da falha.
    schedule.timezone = "America/Sao_Paulo"
    db_session.commit()
    with freeze_time("2026-03-10 11:00:00"):
        service._fire(medication.id, schedule.id)
    notify.assert_called_once()


def test_ct42_fire_does_not_duplicate_reminder_for_same_instant(db_session, session_factory):
    medication, schedule = _seed_medication(db_session, start_date=date(2026, 1, 1))
    notify = MagicMock()
    service = SchedulerService(notify_callback=notify, session_factory=session_factory)

    with freeze_time("2026-03-10 11:00:00"):
        service._fire(medication.id, schedule.id)
        service._fire(medication.id, schedule.id)

    assert db_session.query(ReminderEvent).filter(ReminderEvent.medication_id == medication.id).count() == 1
    notify.assert_called_once()
