"""
Heurística: **Testes de Strings** (Elisabeth Hendrickson — Test Heuristics Cheat Sheet).

Strings longas, caracteres acentuados, caracteres asiáticos, delimitadores, campo em
branco, espaços no início e no fim, injeção de SQL — aplicados aos campos de texto que o
bot pede durante o cadastro.

Casos CT-BOT-S01 a CT-BOT-S10.
"""

import pytest
from telegram.ext import ConversationHandler

from bot.handlers import medications as med
from database.models import Medication

from suporte import dados
from suporte.conversa import Conversa

pytestmark = pytest.mark.strings


@pytest.mark.parametrize('em_branco', [dados.EM_BRANCO, dados.SO_ESPACOS])
async def test_ct_bot_s01_nome_em_branco_e_recusado(fabrica_de_sessao, em_branco):
    """CT-BOT-S01 · heurística "em branco": vazio e só-espaços não passam."""
    pessoa = await Conversa().iniciar()

    await pessoa.digitar(em_branco)

    assert pessoa.disse('não pode ficar em branco')
    assert pessoa.estado == med.NAME


async def test_ct_bot_s02_espacos_nas_bordas_sao_removidos(fabrica_de_sessao, db):
    """CT-BOT-S02 · heurística "espaços no início ou fim".

    O bot faz `strip()` antes de gravar. Vale registrar o contraste: pela API e pelo
    portal web o mesmo nome entra com os espaços (risco R3 do relatório de sessão) —
    quem entra pelo bot fica com um dado mais limpo do que quem entra pelo portal.
    """
    await Conversa().cadastrar(nome=dados.ESPACOS_NAS_BORDAS)

    gravado = db.query(Medication).one()
    assert gravado.name == 'Losartana'


@pytest.mark.parametrize(
    'texto',
    [dados.ACENTUADO, dados.ASIATICO, dados.DELIMITADORES],
    ids=['acentuado', 'asiatico', 'delimitadores'],
)
async def test_ct_bot_s03_caracteres_especiais_sao_preservados(fabrica_de_sessao, db, texto):
    """CT-BOT-S03 · heurísticas "caracteres acentuados", "asiáticos" e "delimitadores"."""
    pessoa = Conversa()
    await pessoa.cadastrar(nome=texto)

    assert pessoa.disse('cadastrado com sucesso')
    assert db.query(Medication).one().name == texto


async def test_ct_bot_s04_injecao_de_sql_fica_sendo_apenas_texto(fabrica_de_sessao, db):
    """CT-BOT-S04 · heurística "injeção de SQL": o comando não é executado."""
    pessoa = Conversa()
    await pessoa.cadastrar(nome=dados.INJECAO_SQL)

    assert db.query(Medication).one().name == dados.INJECAO_SQL

    # E a tabela continua de pé: um cadastro seguinte funciona normalmente.
    outra = Conversa()
    await outra.cadastrar(nome='Depois da injeção')
    assert db.query(Medication).count() == 2


async def test_ct_bot_s05_nome_no_limite_de_200_caracteres_e_aceito(fabrica_de_sessao, db):
    """CT-BOT-S05 · heurística "strings longas", na borda que deve passar."""
    nome = dados.TEXTO_LONGO(200)
    pessoa = Conversa()

    await pessoa.cadastrar(nome=nome)

    assert pessoa.disse('cadastrado com sucesso')
    assert len(db.query(Medication).one().name) == 200


async def test_ct_bot_s06_nome_acima_do_limite_descarta_o_cadastro_inteiro(fabrica_de_sessao, db):
    """CT-BOT-S06 · heurística "strings longas", um caractere além do limite.

    O bot explica o motivo e não grava nada — correto. O que vale registrar é o custo:
    a conversa é encerrada e TODO o rascunho é descartado, então a pessoa recomeça do
    primeiro campo. Em um público idoso, esse é um retrabalho caro.
    """
    pessoa = await Conversa().ate_a_confirmacao(nome=dados.TEXTO_LONGO(201))

    await pessoa.tocar('cadastro:salvar')

    assert pessoa.disse('Não foi possível salvar')
    assert db.query(Medication).count() == 0
    assert pessoa.estado == ConversationHandler.END
    assert 'cadastro' not in pessoa.contexto.user_data  # rascunho perdido


async def test_ct_bot_s07_observacao_no_limite_e_acima_dele(fabrica_de_sessao, db):
    """CT-BOT-S07 · "strings longas" no campo livre de observações (limite de 500)."""
    no_limite = Conversa()
    await no_limite.cadastrar(observacoes=dados.TEXTO_LONGO(500))
    assert no_limite.disse('cadastrado com sucesso')

    acima = await Conversa().ate_a_confirmacao(observacoes=dados.TEXTO_LONGO(501))
    await acima.tocar('cadastro:salvar')
    assert acima.disse('Não foi possível salvar')

    assert db.query(Medication).count() == 1


@pytest.mark.parametrize(
    ('campo', 'trecho_esperado'),
    [('dosagem', 'dosagem não pode ficar em branco'), ('quantidade', 'quantidade não pode ficar em branco')],
)
async def test_ct_bot_s08_dosagem_e_quantidade_em_branco(fabrica_de_sessao, campo, trecho_esperado):
    """CT-BOT-S08 · heurística "em branco" nos outros campos obrigatórios."""
    pessoa = await Conversa().ate_a_dosagem()
    if campo == 'quantidade':
        await pessoa.digitar('50mg')

    await pessoa.digitar(dados.SO_ESPACOS)

    assert pessoa.disse(trecho_esperado)


async def test_ct_bot_s09_observacao_pular_grava_sem_observacao(fabrica_de_sessao, db):
    """CT-BOT-S09 · a palavra reservada 'pular' não vira texto da observação."""
    await Conversa().cadastrar(observacoes='pular')

    assert db.query(Medication).one().instructions is None


async def test_ct_bot_s10_observacao_com_a_palavra_pular_no_meio_e_gravada(fabrica_de_sessao, db):
    """CT-BOT-S10 · heurística "adote abordagem contrária" aplicada à palavra reservada."""
    await Conversa().cadastrar(observacoes='Não pular a dose da noite')

    assert db.query(Medication).one().instructions == 'Não pular a dose da noite'
