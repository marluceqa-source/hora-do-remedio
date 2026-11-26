"""Mascaramento de segredos no log (card #47).

O vazamento que originou este arquivo não foi encontrado por teste nenhum: ele foi encontrado
ao conferir o critério de aceite nº 19 e olhar o arquivo de log em disco. Estes testes existem
para que **não volte** — em particular o `test_token_do_telegram_na_url_do_httpx`, que reproduz
exatamente a linha que o `httpx` emitia.
"""

import logging

import pytest

from core.log_redaction import REDACTED, SecretRedactingFilter, mask_secrets

# Token com a forma real (id numérico : segredo), inventado para o teste.
_TOKEN = "9031798481:AAFdeToKenFaLsOdEtEsTe_12345678901"
_ID = "9031798481"


# --- A função de mascaramento ---------------------------------------------------------


def test_token_do_telegram_na_url_do_httpx():
    """A linha exata que vazou 26.482 vezes."""
    linha = f'HTTP Request: POST https://api.telegram.org/bot{_TOKEN}/sendMessage "HTTP/1.1 200 OK"'

    masked = mask_secrets(linha)

    assert _TOKEN not in masked
    assert "AAFdeToKen" not in masked
    # O que sobra continua dizendo qual bot e qual chamada falhou.
    assert f"bot{_ID}:{REDACTED}" in masked
    assert "/sendMessage" in masked
    assert "HTTP/1.1 200 OK" in masked


@pytest.mark.parametrize(
    "metodo", ["getMe", "getUpdates", "sendMessage", "sendAudio", "sendPhoto", "answerCallbackQuery"]
)
def test_mascara_em_qualquer_metodo_da_api(metodo):
    masked = mask_secrets(f"https://api.telegram.org/bot{_TOKEN}/{metodo}")

    assert _TOKEN not in masked
    assert f"/{metodo}" in masked


def test_mascara_token_solto_sem_o_prefixo_bot():
    """Alguém pode logar o token sem a URL — `logger.info("token=%s", token)`."""
    masked = mask_secrets(f"token configurado: {_TOKEN}")

    assert _TOKEN not in masked
    assert REDACTED in masked


def test_mascara_segredos_literais_da_configuracao():
    segredo = "k4nF2sLq9vTbX7wZpYmR8cJhE1aGdU6o"

    masked = mask_secrets(f"assinando com {segredo}", extra=(segredo,))

    assert segredo not in masked
    assert REDACTED in masked


def test_nao_mascara_valor_vazio_nem_curto():
    """Substituir `""` casaria em toda posição; um segredo de 3 letras casaria dentro de palavras."""
    texto = "mensagem comum sem segredo"

    assert mask_secrets(texto, extra=("", "abc")) == texto


def test_texto_sem_segredo_passa_intacto():
    texto = "Lembrete agendado para 08:00 no fuso America/Sao_Paulo"

    assert mask_secrets(texto) == texto


# --- O filtro, do jeito que roda em produção ------------------------------------------


def _captura(msg: str, args: tuple = (), extra_secrets: tuple[str, ...] = ()) -> str:
    """Emite `msg % args` por um handler com o filtro e devolve o texto escrito."""
    import io

    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(logging.Formatter("%(name)s | %(message)s"))
    handler.addFilter(SecretRedactingFilter(extra_secrets))

    logger = logging.getLogger(f"teste_redacao_{id(buffer)}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.addHandler(handler)
    try:
        logger.info(msg, *args)
    finally:
        logger.removeHandler(handler)
        handler.close()
    return buffer.getvalue()


def test_filtro_mascara_a_mensagem_escrita():
    saida = _captura(f"POST https://api.telegram.org/bot{_TOKEN}/getMe")

    assert _TOKEN not in saida
    assert REDACTED in saida


def test_filtro_mascara_token_vindo_pelos_argumentos():
    """O caso que uma implementação ingênua erra.

    `record.getMessage()` junta `msg % args`. Quem reescreve só `record.msg` e deixa `args`
    intactos faz o handler interpolar de novo — e o token volta.
    """
    saida = _captura("chamando %s com %s", args=("sendMessage", _TOKEN))

    assert _TOKEN not in saida
    assert "sendMessage" in saida


def test_filtro_nunca_descarta_registro():
    """Um log que desaparece é tão ruim quanto um log que vaza."""
    saida = _captura("falha de comunicação com o Telegram")

    assert "falha de comunicação com o Telegram" in saida


def test_filtro_mascara_o_traceback():
    registro = logging.LogRecord("x", logging.ERROR, __file__, 0, "erro", (), None)
    registro.exc_text = f"ConnectError on https://api.telegram.org/bot{_TOKEN}/getUpdates"

    SecretRedactingFilter().filter(registro)

    assert _TOKEN not in registro.exc_text
    assert REDACTED in registro.exc_text


# --- A fiação: o filtro está mesmo instalado? -----------------------------------------


def test_configure_logging_instala_o_filtro_em_todos_os_handlers():
    """Sem esta asserção, o módulo poderia estar perfeito e desligado."""
    import core.logging_config as logging_config

    logging_config._configured = False
    raiz = logging.getLogger()
    handlers_antes = list(raiz.handlers)
    try:
        logging_config.configure_logging()
        novos = [h for h in raiz.handlers if h not in handlers_antes]

        assert novos, "configure_logging não adicionou handler nenhum"
        for handler in novos:
            assert any(
                isinstance(f, SecretRedactingFilter) for f in handler.filters
            ), f"handler {handler!r} ficou sem o filtro de mascaramento"
    finally:
        for handler in [h for h in raiz.handlers if h not in handlers_antes]:
            raiz.removeHandler(handler)
            handler.close()
        logging_config._configured = False
