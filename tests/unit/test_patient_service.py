"""services/patient_service.py: cadastro de pacientes e vínculo com o Telegram (RF03, RF04)."""

from datetime import datetime, timedelta, timezone

import pytest

from database.models import PatientInvitation, Professional
from services import patient_service


def _professional(db_session, email: str = "medica@example.com") -> Professional:
    professional = Professional(
        full_name="Dra. Teste",
        email=email,
        password_hash="x",
        role="medico",
        profession="Médico",
    )
    db_session.add(professional)
    db_session.commit()
    return professional


def test_create_patient_links_the_creating_professional(db_session):
    professional = _professional(db_session)
    patient = patient_service.create_patient(
        db_session, professional, full_name="Paciente Um", internal_identifier="PAC-001"
    )

    authorized = patient_service.list_authorized_patients(db_session, professional)
    assert [p.id for p in authorized] == [patient.id]


def test_create_patient_duplicate_identifier_raises(db_session):
    professional = _professional(db_session)
    patient_service.create_patient(db_session, professional, full_name="Paciente Um", internal_identifier="PAC-DUP")

    with pytest.raises(patient_service.DuplicateInternalIdentifierError):
        patient_service.create_patient(
            db_session, professional, full_name="Outro Nome", internal_identifier="PAC-DUP"
        )


def test_rn22_professional_without_link_cannot_see_patient(db_session):
    owner = _professional(db_session, email="dono@example.com")
    stranger = _professional(db_session, email="estranho@example.com")
    patient = patient_service.create_patient(db_session, owner, full_name="Paciente", internal_identifier="PAC-002")

    assert patient_service.get_authorized_patient(db_session, owner, patient.id) is not None
    assert patient_service.get_authorized_patient(db_session, stranger, patient.id) is None
    assert patient_service.list_authorized_patients(db_session, stranger) == []


def test_create_invite_sets_telegram_link_status_invited(db_session):
    professional = _professional(db_session)
    patient = patient_service.create_patient(db_session, professional, full_name="Paciente", internal_identifier="PAC-003")

    invite, raw_token = patient_service.create_invite(db_session, professional, patient)

    assert raw_token
    db_session.refresh(patient)
    assert patient.telegram_link_status == "invited"
    assert patient_service.find_valid_invite(db_session, raw_token).id == invite.id


def test_create_invite_for_already_linked_patient_raises(db_session):
    professional = _professional(db_session)
    patient = patient_service.create_patient(db_session, professional, full_name="Paciente", internal_identifier="PAC-004")
    _invite, raw_token = patient_service.create_invite(db_session, professional, patient)
    invite = patient_service.find_valid_invite(db_session, raw_token)
    patient_service.confirm_invite_link(db_session, invite, telegram_user_id=700001)

    with pytest.raises(patient_service.PatientAlreadyLinkedError):
        patient_service.create_invite(db_session, professional, patient)


def test_find_valid_invite_rejects_expired_token(db_session):
    professional = _professional(db_session)
    patient = patient_service.create_patient(db_session, professional, full_name="Paciente", internal_identifier="PAC-005")
    invite, raw_token = patient_service.create_invite(db_session, professional, patient)

    invite.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    db_session.commit()

    assert patient_service.find_valid_invite(db_session, raw_token) is None


def test_confirm_invite_link_cannot_be_reused(db_session):
    professional = _professional(db_session)
    patient = patient_service.create_patient(db_session, professional, full_name="Paciente", internal_identifier="PAC-006")
    _invite, raw_token = patient_service.create_invite(db_session, professional, patient)
    invite = patient_service.find_valid_invite(db_session, raw_token)

    patient_service.confirm_invite_link(db_session, invite, telegram_user_id=700002)

    # RN24: convite consumido não pode ser reutilizado.
    assert patient_service.find_valid_invite(db_session, raw_token) is None


def test_confirm_invite_link_rejects_telegram_account_already_linked_elsewhere(db_session):
    professional = _professional(db_session)
    patient_a = patient_service.create_patient(db_session, professional, full_name="Paciente A", internal_identifier="PAC-007")
    patient_b = patient_service.create_patient(db_session, professional, full_name="Paciente B", internal_identifier="PAC-008")

    _invite_a, token_a = patient_service.create_invite(db_session, professional, patient_a)
    patient_service.confirm_invite_link(db_session, patient_service.find_valid_invite(db_session, token_a), telegram_user_id=700003)

    _invite_b, token_b = patient_service.create_invite(db_session, professional, patient_b)
    invite_b = patient_service.find_valid_invite(db_session, token_b)
    with pytest.raises(patient_service.PatientAlreadyLinkedError):
        patient_service.confirm_invite_link(db_session, invite_b, telegram_user_id=700003)


def test_get_valid_invite_by_id_matches_find_valid_invite(db_session):
    professional = _professional(db_session)
    patient = patient_service.create_patient(db_session, professional, full_name="Paciente", internal_identifier="PAC-009")
    invite, raw_token = patient_service.create_invite(db_session, professional, patient)

    by_token = patient_service.find_valid_invite(db_session, raw_token)
    by_id = patient_service.get_valid_invite_by_id(db_session, invite.id)
    assert by_token.id == by_id.id


def test_build_telegram_deep_link_depends_on_settings():
    from unittest.mock import MagicMock, patch

    with patch("services.patient_service.get_settings", return_value=MagicMock(telegram_bot_username="")):
        assert patient_service.build_telegram_deep_link("abc") is None

    with patch("services.patient_service.get_settings", return_value=MagicMock(telegram_bot_username="meu_bot")):
        assert patient_service.build_telegram_deep_link("abc") == "https://t.me/meu_bot?start=abc"
