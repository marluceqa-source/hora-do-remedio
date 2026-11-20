"""services/dashboard_service.py: painel operacional do profissional (RF02)."""

from datetime import date, datetime, time, timedelta

from api.schemas.schedule import ScheduleCreate
from database.models import Professional, ReminderEvent
from services import dashboard_service, patient_service, treatment_service


def _medico(db_session, email: str = "dash.medico@example.com") -> Professional:
    professional = Professional(full_name="Dr. Dash", email=email, password_hash="x", role="medico", profession="Médico")
    db_session.add(professional)
    db_session.commit()
    return professional


def test_dashboard_with_no_patients_is_all_zero(db_session):
    professional = _medico(db_session)
    data = dashboard_service.compute_dashboard(db_session, professional)
    assert data == {
        "total_patients": 0,
        "active_treatments": 0,
        "treatments_ending_soon": 0,
        "reminders_sent": 0,
        "doses_confirmed": 0,
        "doses_not_taken": 0,
        "doses_unconfirmed": 0,
    }


def test_dashboard_counts_active_and_ending_soon_treatments(db_session):
    professional = _medico(db_session)
    patient = patient_service.create_patient(db_session, professional, full_name="Paciente", internal_identifier="DASH-001")
    _invite, raw_token = patient_service.create_invite(db_session, professional, patient)
    invite = patient_service.find_valid_invite(db_session, raw_token)
    patient_service.confirm_invite_link(db_session, invite, 930001)

    ending_soon = treatment_service.create_treatment_medication(
        db_session, professional, patient, medication_name="A", dosage="1mg",
        quantity_per_administration="1", start_date=date.today(),
        end_date=date.today() + timedelta(days=3),
        schedules=[ScheduleCreate(recurrence_type="daily", schedule_time=time(8, 0))],
    )
    far_away = treatment_service.create_treatment_medication(
        db_session, professional, patient, medication_name="B", dosage="2mg",
        quantity_per_administration="1", start_date=date.today(),
        end_date=date.today() + timedelta(days=60),
        schedules=[ScheduleCreate(recurrence_type="daily", schedule_time=time(9, 0))],
    )
    treatment_service.activate_treatment_medication(db_session, professional, ending_soon)
    treatment_service.activate_treatment_medication(db_session, professional, far_away)

    data = dashboard_service.compute_dashboard(db_session, professional)
    assert data["total_patients"] == 1
    assert data["active_treatments"] == 2
    assert data["treatments_ending_soon"] == 1


def test_dashboard_counts_reminder_statuses(db_session):
    professional = _medico(db_session)
    patient = patient_service.create_patient(db_session, professional, full_name="Paciente", internal_identifier="DASH-002")
    _invite, raw_token = patient_service.create_invite(db_session, professional, patient)
    invite = patient_service.find_valid_invite(db_session, raw_token)
    patient_service.confirm_invite_link(db_session, invite, 930002)

    treatment = treatment_service.create_treatment_medication(
        db_session, professional, patient, medication_name="A", dosage="1mg",
        quantity_per_administration="1", start_date=date.today(),
        schedules=[ScheduleCreate(recurrence_type="daily", schedule_time=time(8, 0))],
    )
    activated = treatment_service.activate_treatment_medication(db_session, professional, treatment)
    medication_id = activated.linked_medication_id

    for status in ("confirmed", "confirmed", "not_taken", "pending", "delivered"):
        db_session.add(
            ReminderEvent(
                medication_id=medication_id,
                scheduled_datetime=datetime.now(),
                delivery_datetime=datetime.now() if status != "pending" else None,
                status=status,
            )
        )
    db_session.commit()

    data = dashboard_service.compute_dashboard(db_session, professional)
    assert data["doses_confirmed"] == 2
    assert data["doses_not_taken"] == 1
    assert data["doses_unconfirmed"] == 2  # pending + delivered
    assert data["reminders_sent"] == 4  # tudo que tem delivery_datetime


def test_dashboard_rn22_isolated_between_professionals(db_session):
    owner = _medico(db_session, "dash.owner@example.com")
    stranger = _medico(db_session, "dash.stranger@example.com")
    patient_service.create_patient(db_session, owner, full_name="Paciente", internal_identifier="DASH-003")

    data = dashboard_service.compute_dashboard(db_session, stranger)
    assert data["total_patients"] == 0


def test_dashboard_patient_id_filter(db_session):
    professional = _medico(db_session)
    patient_a = patient_service.create_patient(db_session, professional, full_name="A", internal_identifier="DASH-004")
    patient_b = patient_service.create_patient(db_session, professional, full_name="B", internal_identifier="DASH-005")

    data = dashboard_service.compute_dashboard(db_session, professional, patient_id=patient_a.id)
    assert data["total_patients"] == 1

    data_all = dashboard_service.compute_dashboard(db_session, professional)
    assert data_all["total_patients"] == 2
