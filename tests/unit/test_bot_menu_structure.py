"""RF11 regra: navegação sem digitação obrigatória — todos os botões do menu principal
precisam estar ligados a um handler de mensagem, sem exigir texto livre (CT24)."""

import os
import re
from unittest.mock import patch

import pytest
from telegram.ext import MessageHandler

from core.config import get_settings

from bot.keyboards.menus import (
    MENU_AJUDA,
    MENU_CONFIG,
    MENU_HISTORICO,
    MENU_HOJE,
    MENU_MEUS_REMEDIOS,
    MENU_OUVIR,
    main_menu_keyboard,
)


def _registered_regex_patterns() -> set[str]:
    os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456:TEST-TOKEN")

    # Este é o único teste que monta a Application de verdade, e o python-telegram-bot
    # exige um token para isso. O setdefault acima não basta: get_settings() tem lru_cache
    # e já foi resolvido no import de outros módulos, então um token ausente (ou vazio) já
    # está em memória — é o caso de quem roda sem .env, de CI, e de depois de revogar o
    # token exposto (#49). A causa aí é ambiente, não produto: o teste é pulado em vez de
    # falhar, e a estrutura do menu continua verificada em qualquer máquina com o .env
    # completo.
    if not get_settings().telegram_bot_token:
        pytest.skip("TELEGRAM_BOT_TOKEN não configurado — ver .env.example (CT24 precisa montar a Application)")

    with patch("services.scheduler_service.SchedulerService.start"):
        from bot.main import build_application

        app = build_application()

    patterns = set()
    for handler in app.handlers[0]:
        if isinstance(handler, MessageHandler):
            pattern = getattr(handler.filters, "pattern", None)
            if pattern is not None:
                patterns.add(pattern.pattern)
    return patterns


def test_ct24_every_main_menu_button_is_wired_to_a_handler():
    keyboard = main_menu_keyboard()
    button_labels = {button.text for row in keyboard.keyboard for button in row}

    expected_labels = {
        MENU_MEUS_REMEDIOS,
        "➕ Adicionar Remédio",
        MENU_HOJE,
        MENU_OUVIR,
        MENU_HISTORICO,
        MENU_CONFIG,
        MENU_AJUDA,
    }
    assert button_labels == expected_labels

    # Cada botão (exceto "Adicionar", que abre a conversa de cadastro por um ConversationHandler)
    # é reconhecido por um MessageHandler dedicado ao próprio texto do botão — nunca por
    # digitação livre — confirmando que a navegação principal não exige leitura/escrita.
    registered_patterns = _registered_regex_patterns()
    for label in (MENU_MEUS_REMEDIOS, MENU_HOJE, MENU_OUVIR, MENU_HISTORICO, MENU_CONFIG, MENU_AJUDA):
        expected_pattern = f"^{re.escape(label)}$"
        assert expected_pattern in registered_patterns, f"{label!r} não está ligado a um MessageHandler dedicado"
