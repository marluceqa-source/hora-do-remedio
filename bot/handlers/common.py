from telegram import Update

from database.models import User
from services.text_to_speech_service import synthesize_to_file


async def reply_with_voice(update: Update, text: str, reply_markup=None) -> None:
    """Envia a mensagem em texto e, em seguida, em áudio (RF01, RF11 regra 2: explicações por áudio)."""
    await update.effective_message.reply_text(text, reply_markup=reply_markup)
    audio_path = synthesize_to_file(text)
    if audio_path is not None:
        with open(audio_path, "rb") as audio_file:
            await update.effective_message.reply_audio(audio_file, caption="🔊 Ouvir novamente")


async def reply_with_optional_confirmation_sound(update: Update, user: User, text: str) -> None:
    """Confirmação sonora após ações (RF11 regra 5), oferecida apenas com o modo acessível ativo."""
    await update.effective_message.reply_text(text)
    if not user.accessibility_mode:
        return
    audio_path = synthesize_to_file(text)
    if audio_path is not None:
        with open(audio_path, "rb") as audio_file:
            await update.effective_message.reply_audio(audio_file)
