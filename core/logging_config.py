import logging
import logging.handlers
from pathlib import Path

from core.config import get_settings

_configured = False


def configure_logging() -> None:
    """Configura logging estruturado. Não registrar conteúdo médico sensível (ver seção 12 do prompt master)."""
    global _configured
    if _configured:
        return

    settings = get_settings()
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    _configured = True
