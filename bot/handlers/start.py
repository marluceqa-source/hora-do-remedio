from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.common import reply_with_voice
from bot.keyboards.menus import main_menu_keyboard, yes_no_keyboard
from database.connection import SessionLocal
from database.models import Patient
from services import patient_service
from services.medication_service import get_or_create_user

WELCOME_TEXT = (
    "💊 Olá! Eu sou o Hora do Remédio! Vou ajudar você a lembrar dos seus remédios.\n\n"
    "Use os botões abaixo para navegar. Você não precisa digitar nada."
)

HELP_TEXT = (
    "❓ Como usar o Hora do Remédio:\n\n"
    "💊 Meus Remédios — veja os medicamentos cadastrados.\n"
    "➕ Adicionar Remédio — cadastre um novo medicamento e seus horários.\n"
    "📅 Remédios de Hoje — veja os lembretes de hoje.\n"
    "🔊 Ouvir Lembretes — ouça novamente os lembretes de hoje.\n"
    "📊 Histórico — veja o que foi confirmado ou não.\n"
    "⚙️ Configurações — ative o modo acessível.\n\n"
    "Se tiver dúvidas, peça ajuda a um cuidador autorizado."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = SessionLocal()
    try:
        get_or_create_user(db, update.effective_user.id)

        # RF04: /start <token> via link de convite (https://t.me/<bot>?start=<token>) ou
        # digitado manualmente — identifica o convite e pede confirmação antes de vincular.
        if context.args:
            invite = patient_service.find_valid_invite(db, context.args[0])
            if invite is None:
                await update.message.reply_text(
                    "⚠️ Este convite não é válido, já expirou ou já foi usado. "
                    "Peça um novo convite à sua equipe de saúde."
                )
            else:
                patient = db.get(Patient, invite.patient_id)
                await update.message.reply_text(
                    "📋 Você foi convidado(a) pela sua equipe de saúde para usar o Hora do Remédio.\n\n"
                    f"Confirma que você é {patient.full_name}?",
                    reply_markup=yes_no_keyboard(
                        f"patient_invite:confirm:{invite.id}", f"patient_invite:cancel:{invite.id}"
                    ),
                )
                return
    finally:
        db.close()
    await reply_with_voice(update, WELCOME_TEXT, reply_markup=main_menu_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply_with_voice(update, HELP_TEXT, reply_markup=main_menu_keyboard())
