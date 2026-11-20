import pytest

from services import caregiver_service, medication_service


def test_grant_access_creates_record(db_session):
    owner = medication_service.get_or_create_user(db_session, 100)
    access = caregiver_service.grant_access(db_session, owner, caregiver_telegram_user_id=200, permission="view")

    assert access.user_id == owner.id
    assert access.permission == "view"
    assert access.revoked_at is None


def test_grant_access_is_idempotent_and_updates_permission(db_session):
    owner = medication_service.get_or_create_user(db_session, 101)
    first = caregiver_service.grant_access(db_session, owner, 201, permission="view")
    second = caregiver_service.grant_access(db_session, owner, 201, permission="manage")

    assert first.id == second.id
    assert second.permission == "manage"


def test_cannot_grant_access_to_self(db_session):
    owner = medication_service.get_or_create_user(db_session, 102)
    with pytest.raises(caregiver_service.CaregiverAccessError):
        caregiver_service.grant_access(db_session, owner, caregiver_telegram_user_id=102)


def test_revoke_access_sets_timestamp_and_excludes_from_active_list(db_session):
    owner = medication_service.get_or_create_user(db_session, 103)
    access = caregiver_service.grant_access(db_session, owner, 203)

    caregiver_service.revoke_access(db_session, access)

    assert access.revoked_at is not None
    assert caregiver_service.list_active_access(db_session, owner) == []


def test_find_patient_access_for_caregiver(db_session):
    owner = medication_service.get_or_create_user(db_session, 104)
    caregiver_service.grant_access(db_session, owner, 204)
    caregiver = medication_service.get_or_create_user(db_session, 204)

    found = caregiver_service.find_patient_access_for_caregiver(db_session, owner.id, caregiver)
    assert found is not None

    stranger = medication_service.get_or_create_user(db_session, 999)
    assert caregiver_service.find_patient_access_for_caregiver(db_session, owner.id, stranger) is None


def test_get_owned_access_denies_other_owner(db_session):
    owner = medication_service.get_or_create_user(db_session, 105)
    access = caregiver_service.grant_access(db_session, owner, 205)
    other_owner = medication_service.get_or_create_user(db_session, 106)

    assert caregiver_service.get_owned_access(db_session, access.id, other_owner) is None
    assert caregiver_service.get_owned_access(db_session, access.id, owner) is not None
