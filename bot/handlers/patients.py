"""Confirmação do vínculo paciente↔Telegram a partir de um convite do profissional (RF04),
e os botões "Ouvir"/"Ver detalhes" enviados quando a equipe de saúde ativa um tratamento (RF06)."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.common import reply_with_voice
from bot.handlers.start import WELCOME_TEXT
from bot.keyboards.menus import main_menu_keyboard
from database.connection import SessionLocal
from database.models import Medication
from services import patient_service
from services.text_to_speech_service import synthesize_to_file


async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    invite_id = int(query.data.split(":")[2])
    db = SessionLocal()
    try:
        invite = patient_service.get_valid_invite_by_id(db, invite_id)
        if invite is None:
            await query.answer("Convite inválido ou expirado.", show_alert=True)
            await query.edit_message_text("⚠️ Este convite não é mais válido. Peça um novo à sua equipe de saúde.")
            return

        try:
            patient = patient_service.confirm_invite_link(db, invite, update.effective_user.id)
        except patient_service.PatientAlreadyLinkedError:
            await query.answer("Esta conta já está vinculada a outro paciente.", show_alert=True)
            await query.edit_message_text(
                "⚠️ Esta conta do Telegram já está vinculada a outro cadastro de paciente."
            )
            return
        patient_name = patient.full_name
    finally:
        db.close()

    await query.answer("✅ Vínculo confirmado!")
    await query.edit_message_text(f"✅ Pronto, {patient_name}! Sua conta foi vinculada à sua equipe de saúde.")
    await reply_with_voice(update, WELCOME_TEXT, reply_markup=main_menu_keyboard())


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Tudo bem, nada foi vinculado. Se precisar, peça um novo convite.")


def _get_owned_treatment_medication(db, medication_id: int, telegram_user_id: int) -> Medication | None:
    """Medicamento prescrito, para o paciente **ler** (RN30).

    RN30: o bot não altera prescrições por conta própria. Os fluxos daqui são só de leitura —
    ouvir em áudio e ver detalhes. Quem prescreve é o profissional, pelo portal. Acrescentar
    aqui qualquer escrita em tratamento quebraria a regra.
    """
    medication = db.get(Medication, medication_id)
    if medication is None or medication.user.telegram_user_id != telegram_user_id:
        return None
    return medication


async def treatment_listen_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    medication_id = int(query.data.split(":", 1)[1])
    db = SessionLocal()
    try:
        medication = _get_owned_treatment_medication(db, medication_id, update.effective_user.id)
        if medication is None:
            await query.answer("Medicamento não encontrado.", show_alert=True)
            return
        text = medication.audio_text or f"{medication.name}, {medication.dosage}, {medication.quantity}."
    finally:
        db.close()

    await query.answer()
    audio_path = synthesize_to_file(text)
    if audio_path is not None:
        with open(audio_path, "rb") as audio_file:
            await query.message.reply_audio(audio_file, caption=text)
    else:
        await query.message.reply_text(text)


async def treatment_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    medication_id = int(query.data.split(":", 1)[1])
    db = SessionLocal()
    try:
        medication = _get_owned_treatment_medication(db, medication_id, update.effective_user.id)
        if medication is None:
            await query.answer("Medicamento não encontrado.", show_alert=True)
            return

        lines = [
            f"💊 {medication.name}",
            f"Dose: {medication.dosage}",
            f"Quantidade: {medication.quantity}",
        ]
        if medication.instructions:
            lines.append(f"Orientações: {medication.instructions}")
        lines.append(f"Início: {medication.start_date.strftime('%d/%m/%Y')}")
        if medication.end_date:
            lines.append(f"Término: {medication.end_date.strftime('%d/%m/%Y')}")
        for schedule in medication.schedules:
            if schedule.recurrence_type == "daily":
                lines.append(f"Horário: diariamente às {schedule.schedule_time.strftime('%H:%M')}")
            elif schedule.recurrence_type == "weekly":
                lines.append(f"Horário: às {schedule.schedule_time.strftime('%H:%M')} em {schedule.weekdays}")
            else:
                lines.append(f"Horário: a cada {schedule.interval_hours}h")
        text = "\n".join(lines)
    finally:
        db.close()

    await query.answer()
    await query.message.reply_text(text)
