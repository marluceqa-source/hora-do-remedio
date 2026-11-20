"""Envio de lembretes via Telegram (RF06).

Roda em uma thread separada do loop assíncrono principal do bot (chamada pelo
APScheduler), por isso cria seu próprio Bot e seu próprio loop de eventos a cada envio.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

from core.config import get_settings
from database.connection import SessionLocal
from database.models import Medication, ReminderEvent
from services.text_to_speech_service import synthesize_to_file

logger = logging.getLogger(__name__)


def _build_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Tomei", callback_data=f"confirm:{reminder_id}"),
                InlineKeyboardButton("⏰ Lembrar Depois", callback_data=f"snooze_menu:{reminder_id}"),
            ],
            [InlineKeyboardButton("❌ Não Tomei", callback_data=f"not_taken:{reminder_id}")],
        ]
    )


def _build_text(reminder: ReminderEvent) -> str:
    medication = reminder.medication
    return (
        "🔊 Está na hora do seu remédio!\n\n"
        f"💊 {medication.name}\n"
        f"Dose: {medication.dosage} — {medication.quantity}\n"
        f"Horário previsto: {reminder.scheduled_datetime.strftime('%H:%M')}\n\n"
        "Confira a fotografia e a quantidade cadastrada."
    )


def _build_audio_text(reminder: ReminderEvent) -> str:
    """RF02: usa a descrição falada cadastrada pelo usuário quando existir; senão, o texto padrão."""
    medication = reminder.medication
    if medication.audio_text:
        return medication.audio_text
    return f"Está na hora do seu remédio: {medication.name}, {medication.dosage}, {medication.quantity}."


async def _send_reminder_async(reminder: ReminderEvent, text: str, audio_path) -> None:
    settings = get_settings()
    medication = reminder.medication
    chat_id = medication.user.telegram_user_id
    keyboard = _build_keyboard(reminder.id)

    async with Bot(token=settings.telegram_bot_token) as bot:
        if medication.photo_path:
            try:
                with open(medication.photo_path, "rb") as photo_file:
                    await bot.send_photo(chat_id=chat_id, photo=photo_file, caption=text, reply_markup=keyboard)
            except OSError:
                logger.warning("Foto não encontrada para medication_id=%s: %s", medication.id, medication.photo_path)
                await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
        else:
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)

        if audio_path is not None:
            with open(audio_path, "rb") as audio_file:
                # Telegram exige .ogg/Opus para "mensagem de voz" (send_voice); sem conversão via
                # ffmpeg (não incluída nesta etapa), usamos send_audio como alternativa 100% local.
                await bot.send_audio(chat_id=chat_id, audio=audio_file, caption="🔊 Ouvir lembrete em áudio")


def _build_registered_keyboard(medication_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔊 Ouvir", callback_data=f"treatment_listen:{medication_id}")],
            [InlineKeyboardButton("📋 Ver detalhes", callback_data=f"treatment_details:{medication_id}")],
        ]
    )


async def _send_medication_registered_async(medication: Medication) -> None:
    settings = get_settings()
    chat_id = medication.user.telegram_user_id
    text = (
        "💊 Olá! Sua equipe de saúde cadastrou um medicamento no Hora do Remédio.\n\n"
        f"Nome: {medication.name}\n"
        f"Quantidade: {medication.quantity}\n\n"
        "Toque no alto-falante para ouvir as informações."
    )
    keyboard = _build_registered_keyboard(medication.id)

    async with Bot(token=settings.telegram_bot_token) as bot:
        if medication.photo_path:
            try:
                with open(medication.photo_path, "rb") as photo_file:
                    await bot.send_photo(chat_id=chat_id, photo=photo_file, caption=text, reply_markup=keyboard)
                    return
            except OSError:
                logger.warning("Foto não encontrada para medication_id=%s: %s", medication.id, medication.photo_path)
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)


def send_medication_registered_notification(medication_id: int, session_factory: sessionmaker = SessionLocal) -> None:
    """RF06 ponto 5: avisa o paciente quando o plano é ativado — só se o canal (Telegram)
    já estiver vinculado e autorizado (quem chama já garante isso antes de ativar)."""
    db = session_factory()
    try:
        medication = db.get(Medication, medication_id)
        if medication is None:
            logger.warning("Tentativa de notificar cadastro de medication_id=%s inexistente", medication_id)
            return
        try:
            asyncio.run(_send_medication_registered_async(medication))
        except TelegramError:
            logger.exception("Falha ao notificar cadastro de medicamento medication_id=%s", medication_id)
    finally:
        db.close()


def send_reminder(reminder_id: int, session_factory: sessionmaker = SessionLocal) -> None:
    db = session_factory()
    try:
        reminder = db.get(ReminderEvent, reminder_id)
        if reminder is None:
            logger.warning("Tentativa de notificar reminder_id=%s inexistente", reminder_id)
            return

        text = _build_text(reminder)
        audio_path = synthesize_to_file(_build_audio_text(reminder))

        try:
            asyncio.run(_send_reminder_async(reminder, text, audio_path))
            reminder.status = "delivered"
            reminder.delivery_datetime = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
        except TelegramError:
            # RN18: falha de envio é registrada, mas não gera lembretes duplicados.
            logger.exception("Falha ao enviar lembrete reminder_id=%s", reminder_id)
    finally:
        db.close()
