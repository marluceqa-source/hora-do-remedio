"""
Guarda do condutor de conversa.

`suporte/conversa.py` sabe qual handler atende cada estado do cadastro. Esse mapa é uma
cópia da configuração real do bot, e cópia envelhece. Este teste compara os dois: se
alguém mexer na conversa do bot, ele falha aqui — e não espalhado por 60 testes.
"""

from bot.handlers import medications as med

from suporte.conversa import HANDLER_DE_BOTAO, HANDLER_DE_TEXTO

# PHOTO_WAIT espera uma FOTO, não texto nem botão: fica fora do condutor de propósito.
ESTADOS_FORA_DO_CONDUTOR = {med.PHOTO_WAIT}


def _callbacks_do_estado(conversa, estado):
    return {handler.callback for handler in conversa.states[estado]}


def test_cada_handler_do_condutor_existe_no_bot():
    conversa = med.build_cadastro_conversation()

    for estado, handler in {**HANDLER_DE_TEXTO, **HANDLER_DE_BOTAO}.items():
        assert estado in conversa.states, f'O bot não tem mais o estado {estado}.'
        assert handler in _callbacks_do_estado(conversa, estado), (
            f'O handler {handler.__name__} não atende mais o estado {estado} no bot.'
        )


def test_o_condutor_cobre_todos_os_estados_da_conversa():
    conversa = med.build_cadastro_conversation()
    cobertos = set(HANDLER_DE_TEXTO) | set(HANDLER_DE_BOTAO) | ESTADOS_FORA_DO_CONDUTOR

    faltando = set(conversa.states) - cobertos
    assert not faltando, f'Estados novos na conversa do bot, ainda sem cobertura: {faltando}'


def test_o_cancelamento_continua_disponivel_em_qualquer_estado():
    conversa = med.build_cadastro_conversation()

    callbacks = {handler.callback for handler in conversa.fallbacks}
    assert med.cancel_cadastro in callbacks
