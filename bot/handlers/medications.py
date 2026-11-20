"""Cadastro de medicamentos via conversa no bot (RF02, RF03, RF04).

Guiado por botões sempre que possível. Nome, dosagem, quantidade, datas e observações
aceitam digitação OU áudio (RF04); a fotografia da embalagem é opcional e passa por
reconhecimento OCR com confirmação explícita (RF03, RN10).
"""

import re
import tempfile
import uuid
from datetime import date, datetime
from pathlib import Path

from pydantic import ValidationError
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from api.schemas.medication import MedicationCreate
from api.schemas.schedule import ScheduleCreate
from bot.keyboards.menus import (
    MENU_ADICIONAR,
    confirm_cancel_keyboard,
    interval_choice_keyboard,
    main_menu_keyboard,
    recurrence_type_keyboard,
    time_choice_keyboard,
    weekdays_keyboard,
    yes_no_keyboard,
)
from database.connection import SessionLocal
from services import medication_service
from services.ocr_service import extract_text
from services.speech_to_text_service import transcribe
from services.text_to_speech_service import synthesize_to_file

UPLOADS_DIR = Path("assets/uploads")

(
    NAME,
    NAME_VOICE_CONFIRM,
    DOSAGE,
    QUANTITY,
    START_DATE,
    END_DATE,
    PHOTO_CHOICE,
    PHOTO_WAIT,
    PHOTO_OCR_CONFIRM,
    RECURRENCE,
    TIME_INPUT,
    WEEKDAY_SELECT,
    INTERVAL_INPUT,
    MORE_SCHEDULES,
    OBSERVATIONS,
    CONFIRM,
) = range(16)


async def _transcribe_voice(update: Update) -> str:
    voice = update.message.voice
    telegram_file = await voice.get_file()
    tmp_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4().hex}.ogg"
    await telegram_file.download_to_drive(str(tmp_path))
    try:
        return transcribe(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def _cadastro(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.setdefault("cadastro", {"schedules": [], "pending_schedule": {}})


async def start_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["cadastro"] = {"schedules": [], "pending_schedule": {}}
    await update.message.reply_text(
        "➕ Vamos cadastrar um novo medicamento.\n\n"
        "Qual o nome do medicamento? Você pode digitar ou enviar um áudio dizendo o nome.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def _advance_from_name(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str) -> int:
    _cadastro(context)["name"] = name
    await update.effective_message.reply_text("Qual a dosagem? (ex.: 500mg)")
    return DOSAGE


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("O nome não pode ficar em branco. Qual o nome do medicamento?")
        return NAME
    return await _advance_from_name(update, context, name)


async def receive_name_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    transcribed = await _transcribe_voice(update)
    if not transcribed:
        # RN11: não assumir valores ausentes ou ambíguos quando a transcrição falhar.
        await update.message.reply_text(
            "Não consegui entender o áudio. Pode tentar novamente ou digitar o nome do medicamento?"
        )
        return NAME
    _cadastro(context)["_pending_name"] = transcribed
    await update.message.reply_text(
        f"Entendi: \"{transcribed}\". Está correto?",
        reply_markup=yes_no_keyboard("name_voice:sim", "name_voice:nao"),
    )
    return NAME_VOICE_CONFIRM


async def receive_name_voice_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "name_voice:nao":
        await query.edit_message_text("Sem problemas. Pode digitar ou enviar outro áudio com o nome do medicamento.")
        return NAME
    transcribed = _cadastro(context).pop("_pending_name")
    await query.edit_message_text(f"💊 Nome confirmado: {transcribed}")
    return await _advance_from_name(update, context, transcribed)


async def receive_dosage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dosage = update.message.text.strip()
    if not dosage:
        await update.message.reply_text("A dosagem não pode ficar em branco. Qual a dosagem?")
        return DOSAGE
    _cadastro(context)["dosage"] = dosage
    await update.message.reply_text("Qual a quantidade por administração? (ex.: 1 comprimido)")
    return QUANTITY


async def receive_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    quantity = update.message.text.strip()
    if not quantity:
        await update.message.reply_text("A quantidade não pode ficar em branco. Qual a quantidade?")
        return QUANTITY
    _cadastro(context)["quantity"] = quantity
    await update.message.reply_text("Quando o tratamento começa? Envie a data DD/MM/AAAA, ou digite 'hoje'.")
    return START_DATE


def _parse_date(text: str) -> date | None:
    text = text.strip().lower()
    if text in ("hoje", "today"):
        return date.today()
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None


async def receive_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    parsed = _parse_date(update.message.text)
    if parsed is None:
        await update.message.reply_text("Data inválida. Envie no formato DD/MM/AAAA, ou digite 'hoje'.")
        return START_DATE
    _cadastro(context)["start_date"] = parsed
    await update.message.reply_text(
        "O tratamento tem data para terminar? Envie a data DD/MM/AAAA, ou digite 'não' para tratamento contínuo."
    )
    return END_DATE


async def receive_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().lower()
    if text in ("não", "nao", "sem data"):
        _cadastro(context)["end_date"] = None
    else:
        parsed = _parse_date(update.message.text)
        if parsed is None:
            await update.message.reply_text("Data inválida. Envie DD/MM/AAAA, ou digite 'não'.")
            return END_DATE
        _cadastro(context)["end_date"] = parsed
    await update.message.reply_text(
        "📷 Quer fotografar a embalagem? Isso me ajuda a te mostrar a foto certa na hora do lembrete.",
        reply_markup=yes_no_keyboard("photo:sim", "photo:nao"),
    )
    return PHOTO_CHOICE


async def receive_photo_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "photo:nao":
        await query.edit_message_text(
            "Sem problemas. Como esse remédio deve ser tomado?", reply_markup=recurrence_type_keyboard()
        )
        return RECURRENCE
    await query.edit_message_text("📷 Envie uma foto da embalagem do medicamento.")
    return PHOTO_WAIT


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo = update.message.photo[-1]  # maior resolução disponível
    telegram_file = await photo.get_file()

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    photo_path = UPLOADS_DIR / f"{uuid.uuid4().hex}.jpg"
    await telegram_file.download_to_drive(str(photo_path))
    _cadastro(context)["photo_path"] = str(photo_path)

    recognized = extract_text(photo_path)
    if not recognized:
        # RF03 ponto 7: reconhecimento incerto — mensagem acessível pedindo auxílio, sem travar o cadastro.
        await update.message.reply_text(
            "Não consegui ler o texto da embalagem, mas vou guardar a fotografia para te ajudar a reconhecer "
            "o remédio depois. Se tiver dúvida, peça ajuda a um cuidador autorizado.\n\n"
            "Como esse remédio deve ser tomado?",
            reply_markup=recurrence_type_keyboard(),
        )
        return RECURRENCE

    await update.message.reply_text(
        f"🔎 Reconheci isto na embalagem: \"{recognized}\".\n\nIsso confere com {_cadastro(context)['name']}?",
        reply_markup=yes_no_keyboard("photo_ocr:sim", "photo_ocr:nao"),
    )
    return PHOTO_OCR_CONFIRM


async def receive_photo_ocr_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # RN10: o texto do OCR é apenas informativo — a confirmação não altera os dados já digitados,
    # servindo só para alertar o usuário em caso de divergência.
    query = update.callback_query
    await query.answer()
    if query.data == "photo_ocr:nao":
        await query.edit_message_text(
            "Sem problemas, vou manter o nome que você digitou e guardar a fotografia mesmo assim."
        )
    else:
        await query.edit_message_text("✅ Fotografia associada ao medicamento.")
    await query.message.reply_text("Como esse remédio deve ser tomado?", reply_markup=recurrence_type_keyboard())
    return RECURRENCE


async def receive_recurrence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    recurrence_type = query.data.split(":", 1)[1]
    _cadastro(context)["pending_schedule"] = {"recurrence_type": recurrence_type}
    if recurrence_type in ("daily", "weekly"):
        await query.edit_message_text("Escolha o horário:", reply_markup=time_choice_keyboard())
        return TIME_INPUT
    await query.edit_message_text("Escolha o intervalo entre as doses:", reply_markup=interval_choice_keyboard())
    return INTERVAL_INPUT


async def receive_time_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    value = query.data.split(":", 1)[1]
    if value == "custom":
        await query.edit_message_text("Digite o horário no formato HH:MM (ex.: 08:30):")
        return TIME_INPUT
    return await _store_time_and_continue(update, context, value, via_callback=True)


async def receive_time_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _store_time_and_continue(update, context, update.message.text.strip(), via_callback=False)


async def _store_time_and_continue(update: Update, context: ContextTypes.DEFAULT_TYPE, value: str, via_callback: bool) -> int:
    try:
        hour_str, minute_str = value.split(":")
        hour, minute = int(hour_str), int(minute_str)
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError
    except ValueError:
        message = "Horário inválido. Digite no formato HH:MM (ex.: 08:30):"
        if via_callback:
            await update.callback_query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return TIME_INPUT

    pending = _cadastro(context)["pending_schedule"]
    pending["schedule_time"] = f"{hour:02d}:{minute:02d}:00"

    if pending["recurrence_type"] == "weekly":
        context.user_data["cadastro"]["weekday_selection"] = set()
        keyboard = weekdays_keyboard(set())
        text = "Em quais dias da semana?"
        if via_callback:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
        return WEEKDAY_SELECT

    return await _finish_schedule(update, context, via_callback)


async def receive_weekday_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    code = query.data.split(":", 1)[1]
    selection: set = context.user_data["cadastro"].setdefault("weekday_selection", set())

    if code == "done":
        if not selection:
            await query.answer("Selecione ao menos um dia.", show_alert=True)
            return WEEKDAY_SELECT
        await query.answer()
        _cadastro(context)["pending_schedule"]["weekdays"] = ",".join(sorted(selection))
        return await _finish_schedule(update, context, via_callback=True)

    await query.answer()
    if code in selection:
        selection.discard(code)
    else:
        selection.add(code)
    await query.edit_message_reply_markup(reply_markup=weekdays_keyboard(selection))
    return WEEKDAY_SELECT


async def receive_interval_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    value = query.data.split(":", 1)[1]
    if value == "custom":
        await query.edit_message_text("Digite o intervalo em horas (um número entre 1 e 24):")
        return INTERVAL_INPUT
    _cadastro(context)["pending_schedule"]["interval_hours"] = int(value)
    return await _finish_schedule(update, context, via_callback=True)


async def receive_interval_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        hours = int(text)
        if not (1 <= hours <= 24):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Intervalo inválido. Digite um número entre 1 e 24.")
        return INTERVAL_INPUT
    _cadastro(context)["pending_schedule"]["interval_hours"] = hours
    return await _finish_schedule(update, context, via_callback=False)


async def _finish_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE, via_callback: bool) -> int:
    cadastro = _cadastro(context)
    cadastro["schedules"].append(cadastro.pop("pending_schedule"))
    cadastro.pop("weekday_selection", None)

    text = "Horário adicionado! Deseja adicionar outro horário para este medicamento?"
    keyboard = yes_no_keyboard("horario:mais", "horario:concluir")
    if via_callback:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)
    return MORE_SCHEDULES


async def receive_more_schedules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "horario:mais":
        await query.edit_message_text("Como esse horário deve se repetir?", reply_markup=recurrence_type_keyboard())
        return RECURRENCE
    await query.edit_message_text("Deseja adicionar alguma observação? Digite o texto, ou digite 'pular'.")
    return OBSERVATIONS


async def receive_observations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    cadastro = _cadastro(context)
    cadastro["instructions"] = None if text.lower() == "pular" else text
    return await _show_summary(update, context)


def _describe_schedule(schedule: dict) -> str:
    if schedule["recurrence_type"] == "daily":
        return f"Diariamente às {schedule['schedule_time'][:5]}"
    if schedule["recurrence_type"] == "weekly":
        return f"Às {schedule['schedule_time'][:5]} em {schedule['weekdays']}"
    return f"A cada {schedule['interval_hours']}h"


async def _show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cadastro = _cadastro(context)
    schedules_text = "\n".join(f"- {_describe_schedule(s)}" for s in cadastro["schedules"])
    end_date = cadastro.get("end_date")
    summary = (
        "Confira os dados antes de salvar:\n\n"
        f"💊 Nome: {cadastro['name']}\n"
        f"Dosagem: {cadastro['dosage']}\n"
        f"Quantidade: {cadastro['quantity']}\n"
        f"Início: {cadastro['start_date'].strftime('%d/%m/%Y')}\n"
        f"Término: {end_date.strftime('%d/%m/%Y') if end_date else 'sem data definida'}\n"
        f"Horários:\n{schedules_text}\n"
        f"Observações: {cadastro.get('instructions') or 'nenhuma'}\n\n"
        "Está tudo certo?"
    )
    await update.message.reply_text(summary, reply_markup=confirm_cancel_keyboard("cadastro:salvar"))
    return CONFIRM


async def confirm_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    cadastro = _cadastro(context)

    db = SessionLocal()
    try:
        user = medication_service.get_or_create_user(db, update.effective_user.id)
        try:
            payload = MedicationCreate(
                name=cadastro["name"],
                dosage=cadastro["dosage"],
                quantity=cadastro["quantity"],
                instructions=cadastro.get("instructions"),
                photo_path=cadastro.get("photo_path"),
                start_date=cadastro["start_date"],
                end_date=cadastro.get("end_date"),
                schedules=[ScheduleCreate(**s) for s in cadastro["schedules"]],
            )
        except ValidationError as exc:
            await query.edit_message_text(f"Não foi possível salvar: {exc.errors()[0]['msg']}")
            context.user_data.pop("cadastro", None)
            return ConversationHandler.END

        medication = medication_service.create_medication(db, user, payload)
        scheduler = context.bot_data.get("scheduler_service")
        if scheduler is not None:
            for schedule in medication.schedules:
                scheduler.add_schedule(schedule)
        medication_name = medication.name
        accessibility_mode = user.accessibility_mode
    finally:
        db.close()

    await query.edit_message_text(f"✅ {medication_name} cadastrado com sucesso!")
    if accessibility_mode:
        audio_path = synthesize_to_file(f"{medication_name} cadastrado com sucesso.")
        if audio_path is not None:
            with open(audio_path, "rb") as audio_file:
                await query.message.reply_audio(audio_file)
    await query.message.reply_text("O que deseja fazer agora?", reply_markup=main_menu_keyboard())
    context.user_data.pop("cadastro", None)
    return ConversationHandler.END


async def cancel_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("cadastro", None)
    query = update.callback_query
    if query is not None:
        await query.answer()
        await query.edit_message_text("Cadastro cancelado.")
        await query.message.reply_text("O que deseja fazer agora?", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("Cadastro cancelado.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


async def list_medications_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = SessionLocal()
    try:
        user = medication_service.get_or_create_user(db, update.effective_user.id)
        medications = medication_service.list_medications(db, user, active=True)
        if not medications:
            await update.message.reply_text("Você ainda não tem medicamentos cadastrados. Use ➕ Adicionar Remédio.")
            return
        lines = [f"💊 {m.name} — {m.dosage} ({m.quantity})" for m in medications]
        await update.message.reply_text("Seus medicamentos:\n\n" + "\n".join(lines))
    finally:
        db.close()


def build_cadastro_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{re.escape(MENU_ADICIONAR)}$"), start_cadastro)],
        states={
            NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name),
                MessageHandler(filters.VOICE, receive_name_voice),
            ],
            NAME_VOICE_CONFIRM: [CallbackQueryHandler(receive_name_voice_confirm, pattern=r"^name_voice:")],
            DOSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_dosage)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_quantity)],
            START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_start_date)],
            END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_end_date)],
            PHOTO_CHOICE: [CallbackQueryHandler(receive_photo_choice, pattern=r"^photo:")],
            PHOTO_WAIT: [MessageHandler(filters.PHOTO, receive_photo)],
            PHOTO_OCR_CONFIRM: [CallbackQueryHandler(receive_photo_ocr_confirm, pattern=r"^photo_ocr:")],
            RECURRENCE: [CallbackQueryHandler(receive_recurrence, pattern=r"^recurrence:")],
            TIME_INPUT: [
                CallbackQueryHandler(receive_time_choice, pattern=r"^time:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time_text),
            ],
            WEEKDAY_SELECT: [CallbackQueryHandler(receive_weekday_toggle, pattern=r"^weekday:")],
            INTERVAL_INPUT: [
                CallbackQueryHandler(receive_interval_choice, pattern=r"^interval:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_interval_text),
            ],
            MORE_SCHEDULES: [CallbackQueryHandler(receive_more_schedules, pattern=r"^horario:")],
            OBSERVATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_observations)],
            CONFIRM: [
                CallbackQueryHandler(confirm_cadastro, pattern=r"^cadastro:salvar$"),
                CallbackQueryHandler(cancel_cadastro, pattern=r"^cadastro:cancelar$"),
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancel_cadastro)],
        name="cadastro_medicamento",
        persistent=False,
    )
