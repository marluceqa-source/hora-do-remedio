"""
Heurística: **Ataques de Tipos de Dados** (Elisabeth Hendrickson — Test Heuristics Cheat Sheet).

Investigada no cadastro de medicamento do bot: dias inválidos, formatos de data, nome já
existente, valores nas bordas das faixas e tempo limite de convite.

Casos CT-BOT-D01 a CT-BOT-D11.
"""

from datetime import date, timedelta

import pytest

from bot.handlers import medications as med
from bot.handlers import start as start_handlers
from database.models import Medication, Schedule
from services import patient_service
from database.models import Professional

from suporte import dados
from suporte.conversa import Conversa
from suporte.fakes import ContextoFalso, respostas, update_de_texto

pytestmark = pytest.mark.dados


async def test_ct_bot_d01_nome_ja_existente_e_aceito_sem_aviso(fabrica_de_sessao, db):
    """CT-BOT-D01 · heurística "nome já existente": cadastrar o mesmo remédio duas vezes."""
    pessoa = Conversa()
    await pessoa.cadastrar(nome='Losartana Fictícia')

    repetido = Conversa(user_id=pessoa.user_id)
    await repetido.cadastrar(nome='Losartana Fictícia')

    # Comportamento atual: os dois convivem, sem aviso de duplicidade.
    assert repetido.disse('cadastrado com sucesso')
    nomes = [m.name for m in db.query(Medication).all()]
    assert nomes == ['Losartana Fictícia', 'Losartana Fictícia']


@pytest.mark.parametrize('data_invalida', dados.DATAS_INVALIDAS)
async def test_ct_bot_d02_dias_inexistentes_no_calendario(fabrica_de_sessao, data_invalida):
    """CT-BOT-D02 · heurística "dias inválidos": 30 de fevereiro, 31 de setembro."""
    pessoa = await Conversa().ate_a_data_de_inicio()

    await pessoa.digitar(data_invalida)

    assert pessoa.disse('Data inválida')
    assert pessoa.estado == med.START_DATE  # continua pedindo a data, não avança


@pytest.mark.parametrize('formato', dados.FORMATOS_DE_DATA_RECUSADOS)
async def test_ct_bot_d03_formatos_de_data_fora_do_combinado(fabrica_de_sessao, formato):
    """CT-BOT-D03 · heurística "formatos de data": só DD/MM/AAAA ou 'hoje' são aceitos."""
    pessoa = await Conversa().ate_a_data_de_inicio()

    await pessoa.digitar(formato)

    assert pessoa.disse('Data inválida')
    assert pessoa.estado == med.START_DATE


@pytest.mark.parametrize('entrada', ['hoje', 'HOJE', 'today', '26/11/2026'])
async def test_ct_bot_d04_formatos_de_data_aceitos(fabrica_de_sessao, entrada):
    """CT-BOT-D04 · o outro lado da heurística: o que o contrato promete aceitar, aceita."""
    pessoa = await Conversa().ate_a_data_de_inicio()

    await pessoa.digitar(entrada)

    assert pessoa.estado == med.END_DATE
    assert pessoa.disse('terminar')


async def test_ct_bot_d05_termino_antes_do_inicio_nao_grava_e_explica(fabrica_de_sessao, db):
    """CT-BOT-D05 · heurística "dias inválidos" na relação entre dois campos."""
    ontem = (date.today() - timedelta(days=1)).strftime('%d/%m/%Y')
    pessoa = await Conversa().ate_a_confirmacao(inicio='hoje', termino=ontem)

    await pessoa.tocar('cadastro:salvar')

    assert pessoa.disse('Não foi possível salvar')
    assert pessoa.disse('end_date não pode ser anterior a start_date')
    assert db.query(Medication).count() == 0


@pytest.mark.parametrize('horario', dados.HORARIOS_INVALIDOS)
async def test_ct_bot_d06_horarios_invalidos(fabrica_de_sessao, horario):
    """CT-BOT-D06 · heurística de faixa: hora fora de 00–23, minuto fora de 00–59, lixo."""
    pessoa = await Conversa().ate_o_horario()

    await pessoa.digitar(horario)

    assert pessoa.disse('Horário inválido')
    assert pessoa.estado == med.TIME_INPUT


@pytest.mark.parametrize('horario', dados.HORARIOS_VALIDOS)
async def test_ct_bot_d07_horarios_nas_bordas_sao_aceitos(fabrica_de_sessao, horario):
    """CT-BOT-D07 · bordas da faixa: 00:00, 23:59 e hora sem zero à esquerda."""
    pessoa = await Conversa().ate_o_horario()

    await pessoa.digitar(horario)

    assert pessoa.estado == med.MORE_SCHEDULES
    assert pessoa.disse('Horário adicionado')


@pytest.mark.parametrize('intervalo', dados.INTERVALOS_INVALIDOS)
async def test_ct_bot_d08_intervalos_invalidos(fabrica_de_sessao, intervalo):
    """CT-BOT-D08 · heurística de faixa no intervalo entre doses (1 a 24 horas)."""
    pessoa = await Conversa().ate_o_horario(recorrencia='interval')

    await pessoa.digitar(intervalo)

    assert pessoa.disse('Intervalo inválido')
    assert pessoa.estado == med.INTERVAL_INPUT


@pytest.mark.parametrize('intervalo', dados.INTERVALOS_VALIDOS)
async def test_ct_bot_d09_intervalos_nas_bordas_sao_aceitos(fabrica_de_sessao, intervalo):
    """CT-BOT-D09 · bordas aceitas: 1 h, 24 h e número com espaços em volta."""
    pessoa = await Conversa().ate_o_horario(recorrencia='interval')

    await pessoa.digitar(intervalo)

    assert pessoa.estado == med.MORE_SCHEDULES


async def test_ct_bot_d10_fuso_do_usuario_e_gravado_no_horario(fabrica_de_sessao, db):
    """CT-BOT-D10 · heurística "diferença de horários entre máquinas": o fuso vai junto."""
    await Conversa().cadastrar(horario='08:00')

    agendamento = db.query(Schedule).one()
    assert agendamento.timezone == 'America/Sao_Paulo'
    assert agendamento.schedule_time.strftime('%H:%M') == '08:00'
    assert agendamento.recurrence_type == 'daily'


async def test_ct_bot_d11_convite_expirado_no_start_avisa_sem_vincular(fabrica_de_sessao, db):
    """CT-BOT-D11 · heurística "tempo limite": convite de vínculo fora do prazo."""
    profissional = Professional(
        full_name='Dra. Cenário', email='cenario.bot@example.com', password_hash='x',
        role='medico', profession='Médica',
    )
    db.add(profissional)
    db.commit()
    paciente = patient_service.create_patient(
        db, profissional, full_name='Paciente Fictício', internal_identifier='BOT-EXPIRADO-001'
    )
    convite, token = patient_service.create_invite(db, profissional, paciente)

    # Envelhece o convite além do prazo.
    convite.expires_at = convite.expires_at - timedelta(days=2)
    db.commit()

    update = update_de_texto(770001, f'/start {token}')
    await start_handlers.start(update, ContextoFalso(args=[token]))

    mensagens = ' '.join(respostas(update))
    assert 'não é válido' in mensagens or 'expirou' in mensagens
    db.refresh(paciente)
    assert paciente.telegram_link_status != 'linked'
