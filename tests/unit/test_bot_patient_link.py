"""Deep-link de convite no /start e confirmação do vínculo paciente↔Telegram (RF04)."""

from unittest.mock import AsyncMock, MagicMock

from bot.handlers import patients as patient_handlers
from bot.handlers import start as start_handlers
from database.models import Professional
from services import patient_service


def _professional(db_session, email: str = "medica.bot@example.com") -> Professional:
    professional = Professional(full_name="Dra. Bot", email=email, password_hash="x", role="medico", profession="Médico")
    db_session.add(professional)
    db_session.commit()
    return professional


def _text_update(user_id: int, args: list[str]) -> MagicMock:
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.reply_text = AsyncMock()
    update.message.reply_audio = AsyncMock()
    update.effective_message = update.message
    return update


def _callback_update(user_id: int, data: str) -> MagicMock:
    update = MagicMock()
    update.effective_user.id = user_id
    update.callback_query.data = data
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.callback_query.message.reply_audio = AsyncMock()
    update.effective_message = update.callback_query.message
    return update


async def test_start_with_valid_invite_token_asks_for_confirmation(db_session, session_factory, monkeypatch):
    monkeypatch.setattr("bot.handlers.start.SessionLocal", session_factory)
    professional = _professional(db_session)
    patient = patient_service.create_patient(db_session, professional, full_name="João da Silva", internal_identifier="BOT-PAC-001")
    _invite, raw_token = patient_service.create_invite(db_session, professional, patient)

    update = _text_update(810001, [raw_token])
    context = MagicMock()
    context.args = [raw_token]

    await start_handlers.start(update, context)

    update.message.reply_text.assert_awaited_once()
    message = update.message.reply_text.call_args.args[0]
    assert "João da Silva" in message
    markup = update.message.reply_text.call_args.kwargs["reply_markup"]
    assert markup is not None


async def test_start_with_invalid_token_shows_error_without_crashing(db_session, session_factory, monkeypatch):
    monkeypatch.setattr("bot.handlers.start.SessionLocal", session_factory)
    update = _text_update(810002, ["token-que-nao-existe"])
    context = MagicMock()
    context.args = ["token-que-nao-existe"]

    await start_handlers.start(update, context)

    # O aviso de convite inválido é mostrado, e o fluxo normal de /start continua (não trava).
    first_message = update.message.reply_text.call_args_list[0].args[0]
    assert "não é válido" in first_message or "expirou" in first_message


async def test_confirm_callback_links_patient_and_sends_welcome(db_session, session_factory, monkeypatch):
    monkeypatch.setattr("bot.handlers.patients.SessionLocal", session_factory)
    professional = _professional(db_session, email="medica.confirma@example.com")
    patient = patient_service.create_patient(
        db_session, professional, full_name="Maria Souza", internal_identifier="BOT-PAC-002"
    )
    invite, raw_token = patient_service.create_invite(db_session, professional, patient)

    update = _callback_update(810003, f"patient_invite:confirm:{invite.id}")
    await patient_handlers.confirm_callback(update, MagicMock())

    db_session.refresh(patient)
    assert patient.telegram_link_status == "linked"
    assert patient.user is not None
    assert patient.user.telegram_user_id == 810003

    update.callback_query.edit_message_text.assert_awaited_once()
    assert "Maria Souza" in update.callback_query.edit_message_text.call_args.args[0]


async def test_confirm_callback_rejects_already_consumed_invite(db_session, session_factory, monkeypatch):
    monkeypatch.setattr("bot.handlers.patients.SessionLocal", session_factory)
    professional = _professional(db_session, email="medica.dupla@example.com")
    patient = patient_service.create_patient(
        db_session, professional, full_name="Pedro Lima", internal_identifier="BOT-PAC-003"
    )
    invite, raw_token = patient_service.create_invite(db_session, professional, patient)
    patient_service.confirm_invite_link(db_session, patient_service.find_valid_invite(db_session, raw_token), 810004)

    update = _callback_update(810005, f"patient_invite:confirm:{invite.id}")
    await patient_handlers.confirm_callback(update, MagicMock())

    update.callback_query.answer.assert_awaited_once()
    assert update.callback_query.answer.call_args.kwargs.get("show_alert") is True


async def test_cancel_callback_does_not_link_anything(db_session, session_factory, monkeypatch):
    monkeypatch.setattr("bot.handlers.patients.SessionLocal", session_factory)
    professional = _professional(db_session, email="medica.cancela@example.com")
    patient = patient_service.create_patient(
        db_session, professional, full_name="Carla Dias", internal_identifier="BOT-PAC-004"
    )
    invite, _raw_token = patient_service.create_invite(db_session, professional, patient)

    update = _callback_update(810006, f"patient_invite:cancel:{invite.id}")
    await patient_handlers.cancel_callback(update, MagicMock())

    db_session.refresh(patient)
    assert patient.telegram_link_status == "invited"
    assert patient.user_id is None
