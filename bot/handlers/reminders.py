import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.common import reply_with_optional_confirmation_sound
from bot.keyboards.menus import snooze_options_keyboard
from database.connection import SessionLocal
from services import medication_service, reminder_service
from services.text_to_speech_service import synthesize_to_file

logger = logging.getLogger(__name__)

_STATUS_LABELS = {
    "pending": "⏳ aguardando",
    "delivered": "⏳ aguardando confirmação",
    "confirmed": "✅ tomado",
    "not_taken": "❌ não tomado",
    "snoozed": "⏰ adiado",
    "expired": "⌛ expirado",
}


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = SessionLocal()
    try:
        user = medication_service.get_or_create_user(db, update.effective_user.id)
        reminders = reminder_service.list_today(db, user)
        if not reminders:
            await update.message.reply_text("Você não tem lembretes programados para hoje.")
            return
        lines = [
            f"💊 {r.medication.name} às {r.scheduled_datetime.strftime('%H:%M')} — "
            f"{_STATUS_LABELS.get(r.status, r.status)}"
            for r in reminders
        ]
        await update.message.reply_text("📅 Lembretes de hoje:\n\n" + "\n".join(lines))
    finally:
        db.close()


async def listen_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = SessionLocal()
    try:
        user = medication_service.get_or_create_user(db, update.effective_user.id)
        pending = [r for r in reminder_service.list_today(db, user) if r.status != "confirmed"]
        if not pending:
            await update.message.reply_text("Não há lembretes pendentes para ouvir hoje.")
            return
        for reminder in pending:
            medication = reminder.medication
            text = medication.audio_text or f"💊 {medication.name}: {medication.dosage}, {medication.quantity}."
            audio_path = synthesize_to_file(text)
            if audio_path is not None:
                with open(audio_path, "rb") as audio_file:
                    await update.message.reply_audio(audio_file, caption=text)
            else:
                await update.message.reply_text(text)
    finally:
        db.close()


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = SessionLocal()
    try:
        user = medication_service.get_or_create_user(db, update.effective_user.id)
        events = reminder_service.get_history(db, user, period="week")
        if not events:
            await update.message.reply_text("Nenhum histórico de doses na última semana.")
            return
        lines = [
            f"{e.scheduled_datetime.strftime('%d/%m %H:%M')} — {e.medication.name} — "
            f"{_STATUS_LABELS.get(e.status, e.status)}"
            for e in events
        ]
        await update.message.reply_text("📊 Histórico (últimos 7 dias):\n\n" + "\n".join(lines))
    finally:
        db.close()


async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    reminder_id = int(query.data.split(":", 1)[1])
    db = SessionLocal()
    try:
        user = medication_service.get_or_create_user(db, update.effective_user.id)
        reminder = reminder_service.get_owned_reminder(db, reminder_id, user)
        if reminder is None:
            await query.answer("Lembrete não encontrado.", show_alert=True)
            return
        try:
            reminder_service.confirm(db, reminder)
        except reminder_service.ReminderAlreadyConfirmedError:
            await query.answer("Essa dose já havia sido confirmada.", show_alert=True)
            return
        medication_name = reminder.medication.name
        await query.answer("✅ Confirmado!")
        await query.edit_message_reply_markup(reply_markup=None)
        await reply_with_optional_confirmation_sound(update, user, f"✅ Registrado: você tomou {medication_name}.")
    finally:
        db.close()


async def snooze_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    reminder_id = int(query.data.split(":", 1)[1])
    await query.message.reply_text("Lembrar em quanto tempo?", reply_markup=snooze_options_keyboard(reminder_id))


async def snooze_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    _, reminder_id_str, minutes_str = query.data.split(":")
    reminder_id, minutes = int(reminder_id_str), int(minutes_str)
    db = SessionLocal()
    try:
        user = medication_service.get_or_create_user(db, update.effective_user.id)
        reminder = reminder_service.get_owned_reminder(db, reminder_id, user)
        if reminder is None:
            await query.answer("Lembrete não encontrado.", show_alert=True)
            return
        try:
            reminder_service.snooze(db, reminder)
        except reminder_service.ReminderAlreadyConfirmedError:
            await query.answer("Essa dose já havia sido confirmada.", show_alert=True)
            return
        scheduler = context.bot_data.get("scheduler_service")
        if scheduler is not None:
            scheduler.schedule_snooze(reminder_id, minutes)
        await query.answer(f"⏰ Vou lembrar você em {minutes} minutos.")
        await query.edit_message_text(f"⏰ Lembrete adiado em {minutes} minutos.")
    finally:
        db.close()


async def not_taken_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    reminder_id = int(query.data.split(":", 1)[1])
    db = SessionLocal()
    try:
        user = medication_service.get_or_create_user(db, update.effective_user.id)
        reminder = reminder_service.get_owned_reminder(db, reminder_id, user)
        if reminder is None:
            await query.answer("Lembrete não encontrado.", show_alert=True)
            return
        try:
            reminder_service.mark_not_taken(db, reminder)
        except reminder_service.ReminderAlreadyConfirmedError:
            await query.answer("Essa dose já havia sido confirmada.", show_alert=True)
            return
        medication_name = reminder.medication.name
        await query.answer("Registrado.")
        await query.edit_message_reply_markup(reply_markup=None)
        await reply_with_optional_confirmation_sound(update, user, f"❌ Registrado: {medication_name} não foi tomado.")
    finally:
        db.close()
