from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database.connection import SessionLocal
from services.medication_service import get_or_create_user


def _settings_keyboard(accessibility_mode: bool) -> InlineKeyboardMarkup:
    label = "🔈 Desativar modo acessível" if accessibility_mode else "🔊 Ativar modo acessível"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(label, callback_data="config:toggle_accessibility")],
            [InlineKeyboardButton("👥 Cuidadores", callback_data="caregiver:menu")],
        ]
    )


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = SessionLocal()
    try:
        user = get_or_create_user(db, update.effective_user.id)
        status = "ativado" if user.accessibility_mode else "desativado"
        await update.message.reply_text(
            f"⚙️ Configurações\n\nModo acessível: {status}.",
            reply_markup=_settings_keyboard(user.accessibility_mode),
        )
    finally:
        db.close()


async def toggle_accessibility_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    db = SessionLocal()
    try:
        user = get_or_create_user(db, update.effective_user.id)
        user.accessibility_mode = not user.accessibility_mode
        db.commit()
        status = "ativado" if user.accessibility_mode else "desativado"
        await query.edit_message_text(
            f"⚙️ Configurações\n\nModo acessível: {status}.",
            reply_markup=_settings_keyboard(user.accessibility_mode),
        )
    finally:
        db.close()
