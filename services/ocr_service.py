"""Reconhecimento de texto em fotografias de embalagens (RF03) — local/offline via Tesseract.

Custo: nenhum (binário local). Privacidade: a imagem nunca sai da máquina. Dependência externa:
requer o binário `tesseract` instalado no sistema (ver requirements.txt e README). Alternativa
em nuvem (ex.: Google Vision, AWS Textract) traria melhor acurácia, mas enviaria fotos de
medicamentos do usuário a terceiros — descartada para manter a privacidade exigida (seção 8).
"""

import logging
from pathlib import Path

import pytesseract
from PIL import Image

from core.config import get_settings

logger = logging.getLogger(__name__)


def extract_text(image_path: Path) -> str:
    """Retorna o texto reconhecido na imagem, ou string vazia se o reconhecimento falhar/for incerto."""
    settings = get_settings()
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    try:
        with Image.open(image_path) as image:
            text = pytesseract.image_to_string(image, lang=settings.ocr_language)
        return text.strip()
    except Exception:
        logger.exception("Falha ao executar OCR em %s", image_path)
        return ""
