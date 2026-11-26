"""Mascaramento de segredos nos registros de log (card #47).

Descoberto na [conferência dos 19 critérios de aceite](../wiki/Conferencia-dos-Criterios-de-Aceite.md),
ao verificar o critério nº 19 — "as configurações sensíveis estiverem protegidas". O `httpx`,
usado internamente pelo `python-telegram-bot`, registra em `INFO` a URL de cada chamada:

    HTTP Request: POST https://api.telegram.org/bot<TOKEN>/sendMessage "HTTP/1.1 200 OK"

O token do bot vai na URL. Com o logger raiz em `INFO`, isso gravou 26.482 linhas com o
segredo em texto claro antes de ser percebido.

**Por que um filtro e não `logging.getLogger("httpx").setLevel(WARNING)`.** Silenciar o `httpx`
resolveria este caso e só este: qualquer outra biblioteca que registre a URL volta a vazar, e
§12 do prompt master pede justamente o registro de "falhas de comunicação" — jogar o `httpx`
para `WARNING` perderia o código de status das chamadas bem-sucedidas. O filtro mantém a linha
útil e tira só o segredo.

**Por que nos handlers e não nos loggers.** Um filtro instalado num logger só vê os registros
emitidos *nele*, não os que sobem por propagação dos filhos — então um filtro no logger raiz
não alcançaria nada vindo de `httpx`. Filtro em handler vê tudo que vai ser escrito.
"""

import logging
import re

# Token do Telegram: <id numérico do bot>:<segredo>. O id não é secreto e é o que identifica
# qual bot falhou, então ele fica; o segredo sai.
_TELEGRAM_IN_URL = re.compile(r"\bbot(\d{4,}):[A-Za-z0-9_-]{20,}")
# O mesmo token solto, sem o prefixo `bot` da URL.
_TELEGRAM_BARE = re.compile(r"\b(\d{8,}):[A-Za-z0-9_-]{30,}\b")

REDACTED = "***"


def mask_secrets(text: str, extra: tuple[str, ...] = ()) -> str:
    """Devolve `text` com tokens e segredos conhecidos substituídos por `***`.

    `extra` são valores literais a remover — os segredos da própria configuração. Valores
    vazios ou curtos são ignorados de propósito: substituir `""` casaria em toda posição da
    string, e um segredo de 3 caracteres casaria dentro de palavras legítimas.
    """
    masked = _TELEGRAM_IN_URL.sub(rf"bot\1:{REDACTED}", text)
    masked = _TELEGRAM_BARE.sub(rf"\1:{REDACTED}", masked)
    for secret in extra:
        if secret and len(secret) >= 8:
            masked = masked.replace(secret, REDACTED)
    return masked


class SecretRedactingFilter(logging.Filter):
    """Filtro de handler que mascara segredos antes de o registro ser escrito.

    Nunca descarta registro: devolve sempre `True`. A função dele é reescrever, não censurar —
    um log que desaparece é tão ruim quanto um log que vaza.
    """

    def __init__(self, extra_secrets: tuple[str, ...] = ()) -> None:
        super().__init__()
        self._extra = tuple(s for s in extra_secrets if s)

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            original = record.getMessage()
        except Exception:  # pragma: no cover - formatação quebrada é problema de quem logou
            return True

        masked = mask_secrets(original, self._extra)
        if masked != original:
            # `getMessage()` junta `msg % args`; ao reescrever a mensagem já interpolada é
            # preciso zerar `args`, senão o handler tentaria interpolar de novo — e o token
            # voltaria pelos argumentos.
            record.msg = masked
            record.args = ()

        if record.exc_text:
            record.exc_text = mask_secrets(record.exc_text, self._extra)

        return True


def secrets_from_settings() -> tuple[str, ...]:
    """Valores de configuração que nunca devem aparecer em log."""
    from core.config import get_settings

    settings = get_settings()
    return (
        settings.telegram_bot_token,
        settings.api_secret_key,
        settings.professional_session_secret_key,
    )
