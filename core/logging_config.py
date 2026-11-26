import logging
import logging.handlers
from pathlib import Path

from core.config import get_settings
from core.log_redaction import SecretRedactingFilter, secrets_from_settings

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

    # Mascara segredos antes de qualquer escrita (§12 do prompt master, card #47). Vai nos
    # **handlers**, e não no logger raiz: filtro de logger não vê registro que sobe por
    # propagação — e é justamente de `httpx`, um logger filho, que vinha o token na URL.
    redactor = SecretRedactingFilter(secrets_from_settings())

    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(redactor)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(redactor)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    _configured = True
