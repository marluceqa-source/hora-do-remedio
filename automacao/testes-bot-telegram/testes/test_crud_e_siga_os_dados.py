"""
Heurísticas gerais: **CRUD** e **Siga os Dados** (Elisabeth Hendrickson).

CRUD: criar, ler, atualizar e deletar mantendo a integridade.
Siga os Dados: mapear a dependência "usuário possui medicamento possui horário possui
lembrete" e conferir se o dado criado em um ponto aparece correto no outro.

Casos CT-BOT-C01 a CT-BOT-C08.
"""

from unittest.mock import MagicMock

import pytest

from bot.handlers import medications as med
from bot.handlers import reminders as reminder_handlers
from database.models import Medication, ReminderEvent, Schedule, User

from suporte import cenarios
from suporte.conversa import Conversa, novo_usuario_telegram
from suporte.fakes import ContextoFalso, respostas, ultima_resposta, update_de_callback, update_de_texto

pytestmark = pytest.mark.crud


async def test_ct_bot_c01_criar_pelo_bot_e_ler_na_lista(fabrica_de_sessao, db):
    """CT-BOT-C01 · CRUD: o que foi criado na conversa aparece em "Meus Remédios"."""
    pessoa = Conversa()
    await pessoa.cadastrar(nome='Enalapril Fictício')

    consulta = update_de_texto(pessoa.user_id, '💊 Meus Remédios')
    await med.list_medications_handler(consulta, ContextoFalso())

    assert 'Enalapril Fictício' in ultima_resposta(consulta)
    assert '50mg' in ultima_resposta(consulta)


async def test_ct_bot_c02_ler_lista_vazia_orienta_a_pessoa(fabrica_de_sessao):
    """CT-BOT-C02 · CRUD: ler antes de criar não pode ser um erro seco."""
    consulta = update_de_texto(novo_usuario_telegram(), '💊 Meus Remédios')

    await med.list_medications_handler(consulta, ContextoFalso())

    resposta = ultima_resposta(consulta)
    assert 'ainda não tem medicamentos' in resposta
    assert 'Adicionar Remédio' in resposta


async def test_ct_bot_c03_siga_os_dados_do_usuario_ate_o_horario(fabrica_de_sessao, db):
    """CT-BOT-C03 · Siga os Dados: usuário → medicamento → horário, tudo amarrado."""
    pessoa = Conversa()
    await pessoa.cadastrar(nome='Metformina Fictícia', horario='20:30')

    usuario = db.query(User).filter(User.telegram_user_id == pessoa.user_id).one()
    remedio = db.query(Medication).one()
    agendamento = db.query(Schedule).one()

    assert remedio.user_id == usuario.id
    assert agendamento.medication_id == remedio.id
    assert agendamento.schedule_time.strftime('%H:%M') == '20:30'


async def test_ct_bot_c04_dois_horarios_no_mesmo_medicamento(fabrica_de_sessao, db):
    """CT-BOT-C04 · CRUD: criar com mais de um horário não duplica o medicamento."""
    pessoa = await Conversa().ate_o_horario()
    await pessoa.digitar('08:00')
    await pessoa.tocar('horario:mais')
    await pessoa.tocar('recurrence:daily')
    await pessoa.digitar('20:00')
    await pessoa.tocar('horario:concluir')
    await pessoa.digitar('pular')
    await pessoa.tocar('cadastro:salvar')

    assert db.query(Medication).count() == 1
    horarios = sorted(s.schedule_time.strftime('%H:%M') for s in db.query(Schedule).all())
    assert horarios == ['08:00', '20:00']


async def test_ct_bot_c05_o_agendador_recebe_os_horarios_criados(fabrica_de_sessao):
    """CT-BOT-C05 · Siga os Dados: o horário gravado também entra no agendador."""
    agendador = MagicMock()
    pessoa = Conversa(bot_data={'scheduler_service': agendador})

    await pessoa.cadastrar()

    assert agendador.add_schedule.call_count == 1


async def test_ct_bot_c06_confirmar_lembrete_muda_o_status_e_aparece_no_historico(fabrica_de_sessao, db):
    """CT-BOT-C06 · CRUD (update) e Siga os Dados: lembrete → confirmação → histórico."""
    dono = cenarios.usuario(db, novo_usuario_telegram())
    remedio = cenarios.medicamento(db, dono, nome='Captopril Fictício')
    lembrete = cenarios.lembrete(db, remedio, status='delivered')

    toque = update_de_callback(dono.telegram_user_id, f'confirm:{lembrete.id}')
    await reminder_handlers.confirm_callback(toque, ContextoFalso())

    db.refresh(lembrete)
    assert lembrete.status == 'confirmed'
    assert lembrete.confirmed_datetime is not None

    historico = update_de_texto(dono.telegram_user_id, '📊 Histórico')
    await reminder_handlers.history(historico, ContextoFalso())
    assert 'Captopril Fictício' in ultima_resposta(historico)
    assert 'tomado' in ultima_resposta(historico)


async def test_ct_bot_c07_lembretes_de_hoje_refletem_o_status(fabrica_de_sessao, db):
    """CT-BOT-C07 · Siga os Dados: a tela de hoje mostra o estado real de cada dose."""
    dono = cenarios.usuario(db, novo_usuario_telegram())
    remedio = cenarios.medicamento(db, dono, nome='Sinvastatina Fictícia')
    cenarios.lembrete(db, remedio, status='confirmed', minutos_atras=120)

    hoje = update_de_texto(dono.telegram_user_id, '📅 Remédios de Hoje')
    await reminder_handlers.today(hoje, ContextoFalso())

    resposta = ultima_resposta(hoje)
    assert 'Sinvastatina Fictícia' in resposta
    assert 'tomado' in resposta


async def test_ct_bot_c08_um_usuario_nao_ve_o_remedio_do_outro(fabrica_de_sessao, db):
    """CT-BOT-C08 · Siga os Dados: a dependência é por usuário, e isso tem que valer."""
    primeira = Conversa()
    await primeira.cadastrar(nome='Remédio da Primeira Pessoa')

    consulta = update_de_texto(novo_usuario_telegram(), '💊 Meus Remédios')
    await med.list_medications_handler(consulta, ContextoFalso())

    assert 'Remédio da Primeira Pessoa' not in ' '.join(respostas(consulta))
    assert 'ainda não tem medicamentos' in ultima_resposta(consulta)
