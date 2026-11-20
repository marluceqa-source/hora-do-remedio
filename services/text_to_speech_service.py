"""Síntese de voz 100% local/offline (RF01, RF06, RF11).

Usa o sintetizador de voz nativo do sistema operacional via pyttsx3 (NSSpeechSynthesizer no
macOS, SAPI5 no Windows, espeak no Linux). Não há custo por chamada e nenhum áudio é enviado
a terceiros. Limitação conhecida: depende de uma voz pt-BR estar instalada no SO; caso
contrário, usa a voz padrão do sistema (configurável via TTS_VOICE_NAME).
"""

import logging
import platform
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

import pyttsx3

from core.config import get_settings

logger = logging.getLogger(__name__)


def _convert_to_telegram_friendly_format(source_path: Path) -> Path:
    """Converte o áudio bruto do pyttsx3 para um formato que o Telegram sabe reproduzir.

    O `.aiff` gerado no macOS (NSSpeechSynthesizer) não é reconhecido pelos clientes do
    Telegram via `sendAudio` — a mensagem chega, mas o áudio não carrega. No macOS usamos o
    `afconvert` (nativo do sistema, sem dependência extra) para gerar `.m4a` (AAC), que o
    Telegram reproduz nativamente. Em outros sistemas, ou se a conversão falhar, devolve o
    arquivo original sem modificação.
    """
    if platform.system() != "Darwin" or shutil.which("afconvert") is None:
        return source_path

    target_path = source_path.with_suffix(".m4a")
    try:
        subprocess.run(
            ["afconvert", "-f", "m4af", "-d", "aac", str(source_path), str(target_path)],
            check=True,
            capture_output=True,
            timeout=30,
        )
        source_path.unlink(missing_ok=True)
        return target_path
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        logger.exception("Falha ao converter áudio TTS para .m4a; enviando o arquivo original")
        return source_path


def _patch_macos_driver(engine: "pyttsx3.Engine") -> None:
    """Contorna um bug de compatibilidade do driver NSSS do pyttsx3 com pyobjc >= 10.

    `NSSpeechDriver` é instanciado via `alloc()/initWithProxy()` (idioma do PyObjC), então o
    `__init__` do Python nunca roda e `_current_text` fica sem existir, causando AttributeError
    no primeiro callback de fala. Definir o atributo manualmente antes de falar evita o erro.
    """
    driver = getattr(getattr(engine, "proxy", None), "_driver", None)
    if driver is not None and not hasattr(driver, "_current_text"):
        driver._current_text = ""


def synthesize_to_file(text: str) -> Path | None:
    settings = get_settings()
    try:
        engine = pyttsx3.init()
        _patch_macos_driver(engine)
        if settings.tts_voice_name:
            for voice in engine.getProperty("voices"):
                if settings.tts_voice_name.lower() in voice.name.lower():
                    engine.setProperty("voice", voice.id)
                    break

        output_dir = Path(tempfile.gettempdir()) / "hora_do_remedio_audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{uuid.uuid4().hex}.aiff"

        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
        engine.stop()

        if not output_path.exists():
            return None
        return _convert_to_telegram_friendly_format(output_path)
    except Exception:
        logger.exception("Falha ao gerar áudio TTS local")
        return None
