"""Transcrição de áudio para texto (RF04) — local/offline via faster-whisper.

Custo: nenhum por chamada (modelo roda na própria máquina). Privacidade: o áudio nunca é
enviado a terceiros. O modelo (ver STT_MODEL_SIZE) é baixado uma única vez do Hugging Face
na primeira execução e fica em cache local. Alternativa em nuvem (ex.: Google Speech-to-Text)
teria menor latência de início, mas enviaria áudios do usuário a terceiros — descartada.
"""

import logging
from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel

from core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model() -> WhisperModel:
    settings = get_settings()
    return WhisperModel(settings.stt_model_size, device="cpu", compute_type="int8")


def transcribe(audio_path: Path) -> str:
    """Retorna o texto transcrito, ou string vazia se a transcrição falhar/for vazia."""
    settings = get_settings()
    try:
        model = _get_model()
        segments, _info = model.transcribe(str(audio_path), language=settings.stt_language)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return text
    except Exception:
        logger.exception("Falha ao transcrever áudio %s", audio_path)
        return ""
