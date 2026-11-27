"""
Dublês de `Update` e `Context` do python-telegram-bot.

O bot nunca é iniciado: cada handler é chamado como uma função comum, recebendo um
`update` falso (que registra o que o bot respondeu) e um `context` com dicionários de
verdade — a conversa de cadastro guarda estado em `context.user_data`, então ali não
serve um MagicMock.
"""

from unittest.mock import AsyncMock, MagicMock


class ContextoFalso:
    """Equivalente mínimo de `ContextTypes.DEFAULT_TYPE` para chamar handlers."""

    def __init__(self, args=None, bot_data=None):
        self.args = list(args or [])
        self.user_data = {}
        self.chat_data = {}
        self.bot_data = dict(bot_data or {})
        self.bot = MagicMock()


def update_de_texto(user_id: int, texto: str = '') -> MagicMock:
    """Mensagem de texto enviada pela pessoa."""
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.text = texto
    update.message.reply_text = AsyncMock()
    update.message.reply_audio = AsyncMock()
    update.effective_message = update.message
    update.callback_query = None
    return update


def update_de_callback(user_id: int, data: str) -> MagicMock:
    """Toque em um botão da conversa (callback query)."""
    update = MagicMock()
    update.effective_user.id = user_id
    update.callback_query.data = data
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.edit_message_reply_markup = AsyncMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.callback_query.message.reply_audio = AsyncMock()
    update.effective_message = update.callback_query.message
    return update


def _textos_de(mock) -> list[str]:
    if mock is None:
        return []
    return [
        chamada.args[0]
        for chamada in getattr(mock, 'call_args_list', [])
        if chamada.args and isinstance(chamada.args[0], str)
    ]


def respostas(update) -> list[str]:
    """Tudo que o bot respondeu neste update, em ordem — texto e edições de mensagem."""
    saida = []
    mensagem = getattr(update, 'message', None)
    if mensagem is not None and not isinstance(mensagem, type(None)):
        saida += _textos_de(getattr(mensagem, 'reply_text', None))

    consulta = getattr(update, 'callback_query', None)
    if consulta is not None:
        saida += _textos_de(getattr(consulta, 'edit_message_text', None))
        saida += _textos_de(getattr(getattr(consulta, 'message', None), 'reply_text', None))
    return saida


def ultima_resposta(update) -> str:
    """Última mensagem que o bot mandou — o que a pessoa vê na tela."""
    todas = respostas(update)
    assert todas, 'O bot não respondeu nada a este update.'
    return todas[-1]


def alertas(update) -> list[str]:
    """Alertas de `query.answer(texto, show_alert=True)` — o balão vermelho do Telegram."""
    consulta = getattr(update, 'callback_query', None)
    if consulta is None:
        return []
    return _textos_de(getattr(consulta, 'answer', None))
