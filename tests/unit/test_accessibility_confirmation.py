"""RF11 regra 5: confirmação sonora após ações, oferecida apenas com o modo acessível ativo (CT29)."""

from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers.common import reply_with_optional_confirmation_sound
from database.models import User


async def test_ct29_sends_audio_when_accessibility_mode_enabled(tmp_path):
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    update.effective_message.reply_audio = AsyncMock()
    user = User(accessibility_mode=True)

    audio_file = tmp_path / "audio.aiff"
    audio_file.write_bytes(b"fake-audio")

    with patch("bot.handlers.common.synthesize_to_file", return_value=audio_file):
        await reply_with_optional_confirmation_sound(update, user, "✅ Registrado")

    update.effective_message.reply_text.assert_awaited_once_with("✅ Registrado")
    update.effective_message.reply_audio.assert_awaited_once()


async def test_ct29_skips_audio_when_accessibility_mode_disabled():
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    update.effective_message.reply_audio = AsyncMock()
    user = User(accessibility_mode=False)

    with patch("bot.handlers.common.synthesize_to_file") as mocked_tts:
        await reply_with_optional_confirmation_sound(update, user, "✅ Registrado")
        mocked_tts.assert_not_called()

    update.effective_message.reply_text.assert_awaited_once_with("✅ Registrado")
    update.effective_message.reply_audio.assert_not_awaited()
