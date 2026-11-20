"""Handlers do bot para os botões de lembrete, com Telegram mockado (CT23, CT25)."""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

from bot.handlers import reminders as reminder_handlers
from database.models import Medication, ReminderEvent, User


def _seed_reminder(db_session, telegram_user_id: int, medication_name: str, photo_path: str | None = None):
    user = User(telegram_user_id=telegram_user_id, timezone="America/Sao_Paulo")
    db_session.add(user)
    db_session.flush()

    medication = Medication(
        user_id=user.id,
        name=medication_name,
        dosage="500mg",
        quantity="1 comprimido",
        start_date=date.today(),
        photo_path=photo_path,
    )
    db_session.add(medication)
    db_session.flush()

    reminder = ReminderEvent(medication_id=medication.id, scheduled_datetime=datetime.now(), status="pending")
    db_session.add(reminder)
    db_session.commit()
    db_session.refresh(reminder)
    return reminder


def _fake_confirm_update(telegram_user_id: int, reminder_id: int) -> MagicMock:
    update = MagicMock()
    update.effective_user.id = telegram_user_id
    update.callback_query.data = f"confirm:{reminder_id}"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_reply_markup = AsyncMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.effective_message = update.callback_query.message
    return update


async def test_ct23_confirm_button_registers_dose_without_typing(db_session, session_factory, monkeypatch):
    monkeypatch.setattr("bot.handlers.reminders.SessionLocal", session_factory)
    reminder = _seed_reminder(db_session, telegram_user_id=801, medication_name="Captopril")

    update = _fake_confirm_update(801, reminder.id)
    await reminder_handlers.confirm_callback(update, MagicMock())

    db_session.refresh(reminder)
    assert reminder.status == "confirmed"
    update.callback_query.answer.assert_awaited_once()
    update.callback_query.message.reply_text.assert_awaited_once()
    assert "Captopril" in update.callback_query.message.reply_text.call_args.args[0]


async def test_ct25_similar_packages_keep_their_own_photo_and_name(db_session, session_factory, monkeypatch):
    monkeypatch.setattr("bot.handlers.reminders.SessionLocal", session_factory)
    reminder_a = _seed_reminder(db_session, 811, "Losartana 50mg", photo_path="/uploads/a.jpg")
    reminder_b = _seed_reminder(db_session, 812, "Losartana 100mg", photo_path="/uploads/b.jpg")

    update_a = _fake_confirm_update(811, reminder_a.id)
    await reminder_handlers.confirm_callback(update_a, MagicMock())

    db_session.refresh(reminder_a)
    db_session.refresh(reminder_b)
    # Confirmar a dose de um medicamento não deve afetar o outro, mesmo com nomes parecidos.
    assert reminder_a.status == "confirmed"
    assert reminder_b.status == "pending"
    assert reminder_a.medication.photo_path == "/uploads/a.jpg"
    assert reminder_b.medication.photo_path == "/uploads/b.jpg"
