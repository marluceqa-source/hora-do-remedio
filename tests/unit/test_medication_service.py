from datetime import date

from api.schemas.medication import MedicationCreate, MedicationUpdate
from api.schemas.schedule import ScheduleCreate
from services import medication_service


def _payload(**overrides) -> MedicationCreate:
    data = {
        "name": "Metformina",
        "dosage": "850mg",
        "quantity": "1 comprimido",
        "start_date": date(2026, 1, 1),
        "schedules": [ScheduleCreate(recurrence_type="daily", schedule_time="08:00:00")],
    }
    data.update(overrides)
    return MedicationCreate(**data)


def test_get_or_create_user_is_idempotent(db_session):
    user1 = medication_service.get_or_create_user(db_session, 42, "America/Sao_Paulo")
    user2 = medication_service.get_or_create_user(db_session, 42, "America/Sao_Paulo")
    assert user1.id == user2.id


def test_create_medication_persists_schedules(db_session):
    user = medication_service.get_or_create_user(db_session, 1)
    medication = medication_service.create_medication(db_session, user, _payload())

    assert medication.id is not None
    assert medication.user_id == user.id
    assert len(medication.schedules) == 1
    assert medication.schedules[0].timezone == user.timezone


def test_update_medication_replaces_schedules(db_session):
    user = medication_service.get_or_create_user(db_session, 2)
    medication = medication_service.create_medication(db_session, user, _payload())

    updated = medication_service.update_medication(
        db_session,
        medication,
        user,
        MedicationUpdate(schedules=[ScheduleCreate(recurrence_type="daily", schedule_time="20:00:00")]),
    )

    assert len(updated.schedules) == 1
    assert updated.schedules[0].schedule_time.strftime("%H:%M") == "20:00"


def test_delete_medication_removes_it(db_session):
    user = medication_service.get_or_create_user(db_session, 3)
    medication = medication_service.create_medication(db_session, user, _payload())
    medication_id = medication.id

    medication_service.delete_medication(db_session, medication)

    remaining = medication_service.list_medications(db_session, user)
    assert all(m.id != medication_id for m in remaining)


def test_list_medications_filters_by_active(db_session):
    user = medication_service.get_or_create_user(db_session, 4)
    active_med = medication_service.create_medication(db_session, user, _payload(name="Ativo"))
    inactive_med = medication_service.create_medication(db_session, user, _payload(name="Inativo"))
    medication_service.update_medication(db_session, inactive_med, user, MedicationUpdate(active=False))

    actives = medication_service.list_medications(db_session, user, active=True)
    assert [m.id for m in actives] == [active_med.id]
