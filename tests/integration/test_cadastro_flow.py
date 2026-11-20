"""Fluxo acessível completo de cadastro, só com botões (texto livre apenas para os campos que
realmente exigem digitação: nome, dosagem, quantidade, datas) — seção 11, CT30."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

from telegram.ext import ConversationHandler

from bot.handlers import medications as med
from database.models import Medication


def _text_update(user_id: int, text: str) -> MagicMock:
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.text = text
    update.message.reply_text = AsyncMock()
    update.effective_message = update.message
    return update


def _callback_update(user_id: int, data: str) -> MagicMock:
    update = MagicMock()
    update.effective_user.id = user_id
    update.callback_query.data = data
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.edit_message_reply_markup = AsyncMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.effective_message = update.callback_query.message
    return update


async def test_ct30_fluxo_acessivel_completo_sem_digitacao_obrigatoria(db_session, session_factory, monkeypatch):
    monkeypatch.setattr("bot.handlers.medications.SessionLocal", session_factory)
    user_id = 820001
    context = MagicMock()
    context.user_data = {}
    context.bot_data = {}

    assert await med.start_cadastro(_text_update(user_id, "/adicionar"), context) == med.NAME
    assert await med.receive_name(_text_update(user_id, "Enalapril"), context) == med.DOSAGE
    assert await med.receive_dosage(_text_update(user_id, "10mg"), context) == med.QUANTITY
    assert await med.receive_quantity(_text_update(user_id, "1 comprimido"), context) == med.START_DATE
    assert await med.receive_start_date(_text_update(user_id, "hoje"), context) == med.END_DATE
    assert await med.receive_end_date(_text_update(user_id, "não"), context) == med.PHOTO_CHOICE

    # A partir daqui, nenhuma etapa exige digitação — apenas toques em botões.
    assert await med.receive_photo_choice(_callback_update(user_id, "photo:nao"), context) == med.RECURRENCE
    assert await med.receive_recurrence(_callback_update(user_id, "recurrence:daily"), context) == med.TIME_INPUT
    assert await med.receive_time_choice(_callback_update(user_id, "time:08:00"), context) == med.MORE_SCHEDULES
    assert (
        await med.receive_more_schedules(_callback_update(user_id, "horario:concluir"), context) == med.OBSERVATIONS
    )
    assert await med.receive_observations(_text_update(user_id, "pular"), context) == med.CONFIRM

    final_state = await med.confirm_cadastro(_callback_update(user_id, "cadastro:salvar"), context)
    assert final_state == ConversationHandler.END

    saved = db_session.query(Medication).filter(Medication.name == "Enalapril").one()
    assert saved.dosage == "10mg"
    assert saved.quantity == "1 comprimido"
    assert saved.start_date == date.today()
    assert saved.end_date is None
    assert len(saved.schedules) == 1
    assert saved.schedules[0].recurrence_type == "daily"
    assert saved.schedules[0].schedule_time.strftime("%H:%M") == "08:00"
