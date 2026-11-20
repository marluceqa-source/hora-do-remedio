"""Testes dos fluxos de foto/OCR e voz/STT no cadastro, com mocks das integrações externas
(seção 11: CT19, CT20, CT21, CT26)."""

from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers import medications as med


def _fake_update_with_photo() -> MagicMock:
    update = MagicMock()
    telegram_file = MagicMock()
    telegram_file.download_to_drive = AsyncMock()
    photo_size = MagicMock()
    photo_size.get_file = AsyncMock(return_value=telegram_file)
    update.message.photo = [photo_size]
    update.message.reply_text = AsyncMock()
    return update


def _fake_callback_update(data: str) -> MagicMock:
    update = MagicMock()
    update.callback_query.data = data
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.effective_message = update.callback_query.message
    return update


async def test_ct19_receive_photo_runs_ocr_and_asks_confirmation(tmp_path):
    update = _fake_update_with_photo()
    context = MagicMock()
    context.user_data = {"cadastro": {"name": "Losartana", "schedules": [], "pending_schedule": {}}}

    with (
        patch("bot.handlers.medications.extract_text", return_value="LOSARTANA 50MG"),
        patch("bot.handlers.medications.UPLOADS_DIR", tmp_path),
    ):
        state = await med.receive_photo(update, context)

    assert state == med.PHOTO_OCR_CONFIRM
    assert context.user_data["cadastro"]["photo_path"].startswith(str(tmp_path))
    update.message.reply_text.assert_awaited_once()
    assert "LOSARTANA 50MG" in update.message.reply_text.call_args.args[0]


async def test_ct19_receive_photo_handles_uncertain_ocr_accessibly(tmp_path):
    update = _fake_update_with_photo()
    context = MagicMock()
    context.user_data = {"cadastro": {"name": "Losartana", "schedules": [], "pending_schedule": {}}}

    with (
        patch("bot.handlers.medications.extract_text", return_value=""),
        patch("bot.handlers.medications.UPLOADS_DIR", tmp_path),
    ):
        state = await med.receive_photo(update, context)

    # RF03 ponto 7: reconhecimento incerto não trava o cadastro, segue para os horários.
    assert state == med.RECURRENCE
    assert "cuidador" in update.message.reply_text.call_args.args[0].lower()
    # A fotografia é guardada mesmo sem leitura de texto bem-sucedida.
    assert context.user_data["cadastro"]["photo_path"].startswith(str(tmp_path))


async def test_ct20_confirma_dados_identificados_por_ocr():
    update = _fake_callback_update("photo_ocr:sim")
    context = MagicMock()
    context.user_data = {"cadastro": {"name": "Losartana"}}

    state = await med.receive_photo_ocr_confirm(update, context)

    assert state == med.RECURRENCE
    update.callback_query.edit_message_text.assert_awaited_once()
    assert "associada" in update.callback_query.edit_message_text.call_args.args[0].lower()


async def test_ct20_rejeita_dados_identificados_por_ocr_mantem_nome_digitado():
    update = _fake_callback_update("photo_ocr:nao")
    context = MagicMock()
    context.user_data = {"cadastro": {"name": "Losartana"}}

    state = await med.receive_photo_ocr_confirm(update, context)

    # RN10: a divergência do OCR não altera o nome já digitado pelo usuário.
    assert state == med.RECURRENCE
    assert context.user_data["cadastro"]["name"] == "Losartana"


async def test_ct21_cadastro_por_voz_pede_confirmacao_antes_de_aceitar():
    update = MagicMock()
    update.message.voice = MagicMock()
    update.message.reply_text = AsyncMock()

    with patch("bot.handlers.medications._transcribe_voice", new=AsyncMock(return_value="Losartana")):
        context = MagicMock()
        context.user_data = {"cadastro": {"schedules": [], "pending_schedule": {}}}
        state = await med.receive_name_voice(update, context)

    assert state == med.NAME_VOICE_CONFIRM
    assert context.user_data["cadastro"]["_pending_name"] == "Losartana"
    assert "Losartana" in update.message.reply_text.call_args.args[0]


async def test_ct21_confirma_nome_reconhecido_por_voz_avanca_para_dosagem():
    update = _fake_callback_update("name_voice:sim")
    context = MagicMock()
    context.user_data = {"cadastro": {"schedules": [], "pending_schedule": {}, "_pending_name": "Losartana"}}

    state = await med.receive_name_voice_confirm(update, context)

    assert state == med.DOSAGE
    assert context.user_data["cadastro"]["name"] == "Losartana"


async def test_ct26_falha_de_reconhecimento_de_fala_pede_para_tentar_novamente():
    update = MagicMock()
    update.message.voice = MagicMock()
    update.message.reply_text = AsyncMock()

    with patch("bot.handlers.medications._transcribe_voice", new=AsyncMock(return_value="")):
        context = MagicMock()
        context.user_data = {"cadastro": {"schedules": [], "pending_schedule": {}}}
        state = await med.receive_name_voice(update, context)

    # RN11: não assumir valores ausentes/ambíguos quando a transcrição falha.
    assert state == med.NAME
    assert "_pending_name" not in context.user_data["cadastro"]
    message = update.message.reply_text.call_args.args[0].lower()
    assert "não consegui entender" in message
