"""services/treatment_service.py: cadastro, ativação, suspensão e versionamento (RF05-RF07)."""

from datetime import date, datetime, time

import pytest

from api.schemas.schedule import ScheduleCreate
from database.models import Medication, Patient, Professional, ReminderEvent, User
from services import patient_service, treatment_service


def _medico(db_session, email: str = "medico@example.com") -> Professional:
    professional = Professional(full_name="Dr. Teste", email=email, password_hash="x", role="medico", profession="Médico")
    db_session.add(professional)
    db_session.commit()
    return professional


def _enfermeiro(db_session, email: str = "enfermeira@example.com") -> Professional:
    professional = Professional(
        full_name="Enf. Teste", email=email, password_hash="x", role="enfermeiro", profession="Enfermeiro"
    )
    db_session.add(professional)
    db_session.commit()
    return professional


def _linked_patient(db_session, professional, identifier: str, telegram_user_id: int) -> Patient:
    patient = patient_service.create_patient(db_session, professional, full_name="Paciente", internal_identifier=identifier)
    _invite, raw_token = patient_service.create_invite(db_session, professional, patient)
    invite = patient_service.find_valid_invite(db_session, raw_token)
    return patient_service.confirm_invite_link(db_session, invite, telegram_user_id)


def _schedule() -> list[ScheduleCreate]:
    return [ScheduleCreate(recurrence_type="daily", schedule_time=time(8, 0))]


def test_create_treatment_medication_is_draft_and_materializes_nothing(db_session):
    professional = _medico(db_session)
    patient = patient_service.create_patient(db_session, professional, full_name="Paciente", internal_identifier="TRT-001")

    treatment = treatment_service.create_treatment_medication(
        db_session,
        professional,
        patient,
        medication_name="Losartana",
        dosage="50mg",
        quantity_per_administration="1 comprimido",
        start_date=date.today(),
        schedules=_schedule(),
    )

    assert treatment.status == "draft"
    assert treatment.linked_medication_id is None
    # RN25: rascunho não gera nenhum Medication/lembrete de verdade.
    assert db_session.query(Medication).count() == 0


def test_activate_requires_medico_role(db_session):
    enfermeiro = _enfermeiro(db_session)
    patient = _linked_patient(db_session, enfermeiro, "TRT-002", 910001)
    treatment = treatment_service.create_treatment_medication(
        db_session, enfermeiro, patient, medication_name="Dipirona", dosage="500mg",
        quantity_per_administration="1 comprimido", start_date=date.today(), schedules=_schedule(),
    )

    with pytest.raises(treatment_service.InsufficientRoleError):
        treatment_service.activate_treatment_medication(db_session, enfermeiro, treatment)


def test_activate_requires_patient_linked_to_telegram(db_session):
    professional = _medico(db_session)
    patient = patient_service.create_patient(db_session, professional, full_name="Paciente", internal_identifier="TRT-003")
    treatment = treatment_service.create_treatment_medication(
        db_session, professional, patient, medication_name="Dipirona", dosage="500mg",
        quantity_per_administration="1 comprimido", start_date=date.today(), schedules=_schedule(),
    )

    with pytest.raises(treatment_service.PatientNotLinkedError):
        treatment_service.activate_treatment_medication(db_session, professional, treatment)


def test_activate_materializes_medication_and_schedule(db_session):
    professional = _medico(db_session)
    patient = _linked_patient(db_session, professional, "TRT-004", 910002)
    treatment = treatment_service.create_treatment_medication(
        db_session, professional, patient, medication_name="Losartana", dosage="50mg", dosage_unit=None,
        quantity_per_administration="1 comprimido", start_date=date.today(), schedules=_schedule(),
        instructions="Tomar com água",
    )

    activated = treatment_service.activate_treatment_medication(db_session, professional, treatment)

    assert activated.status == "active"
    assert activated.treatment_plan.status == "active"
    medication = db_session.get(Medication, activated.linked_medication_id)
    assert medication is not None
    assert medication.name == "Losartana"
    assert medication.user_id == patient.user_id
    assert medication.active is True
    assert len(medication.schedules) == 1
    assert "Losartana" in medication.audio_text


def test_cannot_activate_twice(db_session):
    professional = _medico(db_session)
    patient = _linked_patient(db_session, professional, "TRT-005", 910003)
    treatment = treatment_service.create_treatment_medication(
        db_session, professional, patient, medication_name="Losartana", dosage="50mg",
        quantity_per_administration="1 comprimido", start_date=date.today(), schedules=_schedule(),
    )
    treatment_service.activate_treatment_medication(db_session, professional, treatment)

    with pytest.raises(treatment_service.InvalidStatusTransitionError):
        treatment_service.activate_treatment_medication(db_session, professional, treatment)


def test_suspend_deactivates_linked_medication(db_session):
    professional = _medico(db_session)
    patient = _linked_patient(db_session, professional, "TRT-006", 910004)
    treatment = treatment_service.create_treatment_medication(
        db_session, professional, patient, medication_name="Losartana", dosage="50mg",
        quantity_per_administration="1 comprimido", start_date=date.today(), schedules=_schedule(),
    )
    activated = treatment_service.activate_treatment_medication(db_session, professional, treatment)

    suspended = treatment_service.suspend_treatment_medication(db_session, activated)

    assert suspended.status == "suspended"
    medication = db_session.get(Medication, suspended.linked_medication_id)
    assert medication.active is False


def test_cannot_suspend_a_draft(db_session):
    professional = _medico(db_session)
    patient = patient_service.create_patient(db_session, professional, full_name="Paciente", internal_identifier="TRT-007")
    treatment = treatment_service.create_treatment_medication(
        db_session, professional, patient, medication_name="Losartana", dosage="50mg",
        quantity_per_administration="1 comprimido", start_date=date.today(), schedules=_schedule(),
    )

    with pytest.raises(treatment_service.InvalidStatusTransitionError):
        treatment_service.suspend_treatment_medication(db_session, treatment)


def test_update_draft_edits_in_place(db_session):
    professional = _medico(db_session)
    patient = patient_service.create_patient(db_session, professional, full_name="Paciente", internal_identifier="TRT-008")
    treatment = treatment_service.create_treatment_medication(
        db_session, professional, patient, medication_name="Losartana", dosage="50mg",
        quantity_per_administration="1 comprimido", start_date=date.today(), schedules=_schedule(),
    )

    updated = treatment_service.update_treatment_medication(
        db_session, treatment, fields={"dosage": "100mg"}, schedules=None
    )

    assert updated.id == treatment.id
    assert updated.dosage == "100mg"
    assert updated.previous_version_id is None


def test_update_active_creates_new_version_preserving_history(db_session):
    professional = _medico(db_session)
    patient = _linked_patient(db_session, professional, "TRT-009", 910005)
    treatment = treatment_service.create_treatment_medication(
        db_session, professional, patient, medication_name="Losartana", dosage="50mg",
        quantity_per_administration="1 comprimido", start_date=date.today(), schedules=_schedule(),
    )
    activated = treatment_service.activate_treatment_medication(db_session, professional, treatment)
    original_medication_id = activated.linked_medication_id

    # Histórico de uma dose já confirmada antes da edição.
    db_session.add(
        ReminderEvent(medication_id=original_medication_id, scheduled_datetime=datetime.now(), status="confirmed")
    )
    db_session.commit()

    new_version = treatment_service.update_treatment_medication(
        db_session, activated, fields={"dosage": "100mg"}, schedules=None
    )

    assert new_version.id != activated.id
    assert new_version.status == "draft"
    assert new_version.previous_version_id == activated.id
    db_session.refresh(activated)
    assert activated.status == "active"  # a versão antiga continua ativa até a nova ser ativada

    reactivated = treatment_service.activate_treatment_medication(db_session, professional, new_version)

    # RN27: mesma linha de Medication é atualizada — o histórico de ReminderEvents não se perde.
    assert reactivated.linked_medication_id == original_medication_id
    db_session.refresh(activated)
    assert activated.status == "closed"
    medication = db_session.get(Medication, original_medication_id)
    assert medication.dosage == "100mg"
    assert db_session.query(ReminderEvent).filter(ReminderEvent.medication_id == original_medication_id).count() == 1


def test_get_version_chain_oldest_to_newest(db_session):
    professional = _medico(db_session)
    patient = _linked_patient(db_session, professional, "TRT-010", 910006)
    treatment = treatment_service.create_treatment_medication(
        db_session, professional, patient, medication_name="Losartana", dosage="50mg",
        quantity_per_administration="1 comprimido", start_date=date.today(), schedules=_schedule(),
    )
    activated = treatment_service.activate_treatment_medication(db_session, professional, treatment)
    new_version = treatment_service.update_treatment_medication(
        db_session, activated, fields={"dosage": "100mg"}, schedules=None
    )

    chain = treatment_service.get_version_chain(db_session, new_version)
    assert [t.id for t in chain] == [activated.id, new_version.id]
