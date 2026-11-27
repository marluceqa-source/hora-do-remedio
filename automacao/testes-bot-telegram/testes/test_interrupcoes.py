"""
Heurística geral: **Interrupções** (Elisabeth Hendrickson) — "simular interrupções como
reinício, timeout, logout".

Uma conversa de 16 passos convive com interrupções o tempo todo: a pessoa desiste, troca
de assunto, toca num botão antigo, ou o bot reinicia no meio.

Casos CT-BOT-I01 a CT-BOT-I07.
"""

import pytest
from telegram.ext import ConversationHandler

from bot.handlers import medications as med
from bot.handlers import reminders as reminder_handlers
from database.models import Medication

from suporte import cenarios
from suporte.conversa import Conversa, novo_usuario_telegram
from suporte.fakes import ContextoFalso, alertas, update_de_callback

pytestmark = pytest.mark.interrupcoes


async def test_ct_bot_i01_cancelar_por_comando_no_meio_descarta_o_rascunho(fabrica_de_sessao, db):
    """CT-BOT-I01 · a pessoa desiste no meio do cadastro com /cancelar."""
    pessoa = await Conversa().ate_o_horario()
    assert pessoa.dados_em_rascunho  # havia um cadastro em andamento

    await pessoa.cancelar_por_comando()

    assert pessoa.disse('Cadastro cancelado')
    assert pessoa.estado == ConversationHandler.END
    assert 'cadastro' not in pessoa.contexto.user_data
    assert db.query(Medication).count() == 0


async def test_ct_bot_i02_cancelar_pelo_botao_na_confirmacao(fabrica_de_sessao, db):
    """CT-BOT-I02 · desistir no último passo, já vendo o resumo."""
    pessoa = await Conversa().ate_a_confirmacao()

    await pessoa.tocar('cadastro:cancelar')

    assert pessoa.disse('Cadastro cancelado')
    assert db.query(Medication).count() == 0


async def test_ct_bot_i03_recomecar_o_cadastro_zera_o_rascunho_anterior(fabrica_de_sessao, db):
    """CT-BOT-I03 · a pessoa troca de assunto e começa de novo, sem ter cancelado."""
    pessoa = await Conversa().ate_o_horario(nome='Remédio Abandonado')

    await pessoa.iniciar()  # tocou em "Adicionar Remédio" de novo
    await pessoa.digitar('Remédio Novo')

    assert pessoa.dados_em_rascunho['name'] == 'Remédio Novo'
    assert pessoa.dados_em_rascunho['schedules'] == []
    assert db.query(Medication).count() == 0


async def test_ct_bot_i04_a_conversa_nao_sobrevive_a_um_reinicio_do_bot(fabrica_de_sessao):
    """CT-BOT-I04 · heurística "reinício".

    A conversa de cadastro é declarada com `persistent=False`: o rascunho vive só na
    memória do processo. Se o bot reiniciar no meio, a pessoa recomeça do primeiro campo.
    É uma decisão de projeto legítima, mas precisa estar registrada — este teste trava
    esse contrato, para a mudança não passar despercebida.
    """
    conversa = med.build_cadastro_conversation()

    assert conversa.persistent is False
    assert conversa.name == 'cadastro_medicamento'


async def test_ct_bot_i05_botao_de_lembrete_ja_encerrado_nao_registra_nada(fabrica_de_sessao, db):
    """CT-BOT-I05 · heurística "tempo limite": a pessoa toca num lembrete antigo (CT17)."""
    dono = cenarios.usuario(db, novo_usuario_telegram())
    remedio = cenarios.medicamento(db, dono)
    lembrete = cenarios.lembrete(db, remedio, status='expired')

    toque = update_de_callback(dono.telegram_user_id, f'confirm:{lembrete.id}')
    await reminder_handlers.confirm_callback(toque, ContextoFalso())

    aviso = ' '.join(alertas(toque))
    assert 'antigo' in aviso and 'Nada foi registrado' in aviso
    db.refresh(lembrete)
    assert lembrete.status == 'expired'  # continua expirado, não virou confirmado


async def test_ct_bot_i06_confirmar_a_mesma_dose_duas_vezes(fabrica_de_sessao, db):
    """CT-BOT-I06 · toque repetido no mesmo botão — acontece muito com mão trêmula."""
    dono = cenarios.usuario(db, novo_usuario_telegram())
    remedio = cenarios.medicamento(db, dono)
    lembrete = cenarios.lembrete(db, remedio, status='delivered')

    primeiro = update_de_callback(dono.telegram_user_id, f'confirm:{lembrete.id}')
    await reminder_handlers.confirm_callback(primeiro, ContextoFalso())

    segundo = update_de_callback(dono.telegram_user_id, f'confirm:{lembrete.id}')
    await reminder_handlers.confirm_callback(segundo, ContextoFalso())

    assert 'já havia sido confirmada' in ' '.join(alertas(segundo))
    db.refresh(lembrete)
    assert lembrete.status == 'confirmed'


async def test_ct_bot_i07_adiar_dose_ja_confirmada_e_recusado(fabrica_de_sessao, db):
    """CT-BOT-I07 · interrupção fora de ordem: adiar o que já foi tomado."""
    dono = cenarios.usuario(db, novo_usuario_telegram())
    remedio = cenarios.medicamento(db, dono)
    lembrete = cenarios.lembrete(db, remedio, status='confirmed')

    toque = update_de_callback(dono.telegram_user_id, f'snooze:{lembrete.id}:15')
    await reminder_handlers.snooze_callback(toque, ContextoFalso())

    assert 'já havia sido confirmada' in ' '.join(alertas(toque))
    db.refresh(lembrete)
    assert lembrete.status == 'confirmed'
    assert lembrete.snooze_count == 0
