"""RF11 regra: navegação sem digitação obrigatória — todos os botões do menu principal
precisam estar ligados a um handler de mensagem, sem exigir texto livre (CT24)."""

import os
import re
from unittest.mock import patch

from telegram.ext import MessageHandler

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
