"""Testes de envio de lembretes com mocks da integração com o Telegram (CT13, CT22, CT27)."""

from datetime import date, datetime
from unittest.mock import AsyncMock, patch

from telegram.error import TelegramError

from database.models import Medication, ReminderEvent, User
from services import notification_service


def _seed_reminder(db_session, telegram_user_id: int = 950, audio_text: str | None = None) -> ReminderEvent:
    user = User(telegram_user_id=telegram_user_id, timezone="America/Sao_Paulo")
    db_session.add(user)
    db_session.flush()

    medication = Medication(
        user_id=user.id,
        name="Losartana",
        dosage="50mg",
        quantity="1 comprimido",
        start_date=date.today(),
        audio_text=audio_text,
    )
    db_session.add(medication)
    db_session.flush()

    reminder = ReminderEvent(medication_id=medication.id, scheduled_datetime=datetime.now(), status="pending")
    db_session.add(reminder)
    db_session.commit()
    db_session.refresh(reminder)
    return reminder


def test_ct22_send_reminder_marks_delivered_on_success(db_session, session_factory):
    reminder = _seed_reminder(db_session)

    with (
        patch("services.notification_service.synthesize_to_file", return_value=None),
        patch("services.notification_service._send_reminder_async", new_callable=AsyncMock) as mocked_send,
    ):
        notification_service.send_reminder(reminder.id, session_factory=session_factory)
        mocked_send.assert_awaited_once()

    db_session.refresh(reminder)
    assert reminder.status == "delivered"
    assert reminder.delivery_datetime is not None


def test_ct13_send_reminder_handles_telegram_failure_without_crashing(db_session, session_factory):
    reminder = _seed_reminder(db_session, telegram_user_id=951)

    with (
        patch("services.notification_service.synthesize_to_file", return_value=None),
        patch(
            "services.notification_service._send_reminder_async",
            new_callable=AsyncMock,
            side_effect=TelegramError("Telegram indisponível"),
        ),
    ):
        notification_service.send_reminder(reminder.id, session_factory=session_factory)

    db_session.refresh(reminder)
    # RN18: a falha é registrada (via log) sem travar o processo nem marcar como entregue.
    assert reminder.status == "pending"
    assert reminder.delivery_datetime is None


def test_send_reminder_ignores_unknown_reminder_id(db_session, session_factory):
    with patch("services.notification_service._send_reminder_async", new_callable=AsyncMock) as mocked_send:
        notification_service.send_reminder(999999, session_factory=session_factory)
        mocked_send.assert_not_awaited()


def test_build_audio_text_uses_custom_description_when_present(db_session):
    custom_text = "Por favor, tomar losartana. Por favor, tomar losartana."
    reminder = _seed_reminder(db_session, telegram_user_id=952, audio_text=custom_text)

    assert notification_service._build_audio_text(reminder) == custom_text


def test_build_audio_text_falls_back_to_default_when_absent(db_session):
    reminder = _seed_reminder(db_session, telegram_user_id=953, audio_text=None)

    audio_text = notification_service._build_audio_text(reminder)
    assert "Losartana" in audio_text
    assert "50mg" in audio_text


def test_send_reminder_synthesizes_the_custom_audio_text(db_session, session_factory):
    custom_text = "Por favor, tomar losartana. Por favor, tomar losartana."
    reminder = _seed_reminder(db_session, telegram_user_id=954, audio_text=custom_text)

    with (
        patch("services.notification_service.synthesize_to_file", return_value=None) as mocked_tts,
        patch("services.notification_service._send_reminder_async", new_callable=AsyncMock),
    ):
        notification_service.send_reminder(reminder.id, session_factory=session_factory)
        mocked_tts.assert_called_once_with(custom_text)
