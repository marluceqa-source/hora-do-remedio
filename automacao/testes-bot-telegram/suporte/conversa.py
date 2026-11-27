"""
Condutor da conversa de cadastro de medicamento.

O bot cadastra um remédio em uma conversa de 16 estados. Repetir essa sequência em cada
teste esconderia o que o teste está realmente investigando, então o percurso mora aqui e
o teste só diz o que foi digitado ou tocado:

    conversa = await Conversa(555).iniciar()
    await conversa.digitar('Losartana')
    await conversa.digitar('50mg')

O mapa de estado → handler é conferido contra o `ConversationHandler` de verdade em
`testes/test_mapa_da_conversa.py`: se o bot mudar a conversa, o teste avisa.
"""

import itertools

from bot.handlers import medications as med

from suporte.fakes import ContextoFalso, respostas, ultima_resposta, update_de_callback, update_de_texto

# Estados em que o bot espera texto digitado.
HANDLER_DE_TEXTO = {
    med.NAME: med.receive_name,
    med.DOSAGE: med.receive_dosage,
    med.QUANTITY: med.receive_quantity,
    med.START_DATE: med.receive_start_date,
    med.END_DATE: med.receive_end_date,
    med.TIME_INPUT: med.receive_time_text,
    med.INTERVAL_INPUT: med.receive_interval_text,
    med.OBSERVATIONS: med.receive_observations,
}

# Estados em que o bot espera o toque em um botão.
HANDLER_DE_BOTAO = {
    med.NAME_VOICE_CONFIRM: med.receive_name_voice_confirm,
    med.PHOTO_CHOICE: med.receive_photo_choice,
    med.PHOTO_OCR_CONFIRM: med.receive_photo_ocr_confirm,
    med.RECURRENCE: med.receive_recurrence,
    med.TIME_INPUT: med.receive_time_choice,
    med.WEEKDAY_SELECT: med.receive_weekday_toggle,
    med.INTERVAL_INPUT: med.receive_interval_choice,
    med.MORE_SCHEDULES: med.receive_more_schedules,
    med.CONFIRM: med.confirm_cadastro,
}

_IDS = itertools.count(700_000_001)


def novo_usuario_telegram() -> int:
    """telegram_user_id único, para um teste nunca enxergar o dado de outro."""
    return next(_IDS)


class Conversa:
    """Uma pessoa conversando com o bot. Guarda o estado da conversa entre as mensagens."""

    def __init__(self, user_id: int | None = None, bot_data: dict | None = None):
        self.user_id = user_id if user_id is not None else novo_usuario_telegram()
        self.contexto = ContextoFalso(bot_data=bot_data)
        self.estado = None
        self.update = None

    async def iniciar(self) -> 'Conversa':
        self.update = update_de_texto(self.user_id, '➕ Adicionar Remédio')
        self.estado = await med.start_cadastro(self.update, self.contexto)
        return self

    async def digitar(self, texto: str) -> 'Conversa':
        handler = HANDLER_DE_TEXTO.get(self.estado)
        assert handler, f'O bot não espera texto no estado {self.estado}.'
        self.update = update_de_texto(self.user_id, texto)
        self.estado = await handler(self.update, self.contexto)
        return self

    async def tocar(self, data: str) -> 'Conversa':
        if self.estado == med.CONFIRM and data.endswith('cancelar'):
            handler = med.cancel_cadastro
        else:
            handler = HANDLER_DE_BOTAO.get(self.estado)
        assert handler, f'O bot não espera botão no estado {self.estado}.'
        self.update = update_de_callback(self.user_id, data)
        self.estado = await handler(self.update, self.contexto)
        return self

    async def cancelar_por_comando(self) -> 'Conversa':
        """O /cancelar é o fallback da conversa — vale em qualquer estado."""
        self.update = update_de_texto(self.user_id, '/cancelar')
        self.update.callback_query = None
        self.estado = await med.cancel_cadastro(self.update, self.contexto)
        return self

    @property
    def resposta(self) -> str:
        """Última mensagem do bot — o que fica na tela."""
        return ultima_resposta(self.update)

    @property
    def respostas(self) -> list[str]:
        """Tudo que o bot respondeu ao último envio, em ordem."""
        return respostas(self.update)

    def disse(self, trecho: str) -> bool:
        """O bot disse isso em alguma das mensagens da última rodada?"""
        return any(trecho.lower() in mensagem.lower() for mensagem in self.respostas)

    @property
    def dados_em_rascunho(self) -> dict:
        return self.contexto.user_data.get('cadastro', {})

    async def ate_a_dosagem(self, nome: str = 'Losartana Fictícia') -> 'Conversa':
        await self.iniciar()
        await self.digitar(nome)
        return self

    async def ate_a_data_de_inicio(self, **campos) -> 'Conversa':
        await self.ate_a_dosagem(campos.get('nome', 'Losartana Fictícia'))
        await self.digitar(campos.get('dosagem', '50mg'))
        await self.digitar(campos.get('quantidade', '1 comprimido'))
        return self

    async def ate_o_horario(self, recorrencia: str = 'daily', **campos) -> 'Conversa':
        await self.ate_a_data_de_inicio(**campos)
        await self.digitar(campos.get('inicio', 'hoje'))
        await self.digitar(campos.get('termino', 'não'))
        await self.tocar('photo:nao')
        await self.tocar(f'recurrence:{recorrencia}')
        return self

    async def ate_a_confirmacao(self, **campos) -> 'Conversa':
        await self.ate_o_horario(**campos)
        await self.digitar(campos.get('horario', '08:00'))
        await self.tocar('horario:concluir')
        await self.digitar(campos.get('observacoes', 'pular'))
        return self

    async def cadastrar(self, **campos) -> 'Conversa':
        """Percurso feliz inteiro, do menu ao 'cadastrado com sucesso'."""
        await self.ate_a_confirmacao(**campos)
        await self.tocar('cadastro:salvar')
        return self
