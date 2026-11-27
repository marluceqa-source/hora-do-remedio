"""
Sabedoria em testes: **Adote abordagem contrária** — "teste o que o sistema não deveria
fazer" (Elisabeth Hendrickson).

Aqui o alvo não é o caminho feliz: é o que acontece quando alguém toca num botão que não
é seu, usa um convite que já foi usado, ou manda o bot fazer o que ele deveria recusar.

Casos CT-BOT-X01 a CT-BOT-X07.
"""

import pytest

from bot.handlers import patients as patient_handlers
from bot.handlers import reminders as reminder_handlers
from bot.handlers import start as start_handlers
from database.models import Patient, Professional
from services import patient_service

from suporte import cenarios
from suporte.conversa import novo_usuario_telegram
from suporte.fakes import ContextoFalso, alertas, respostas, update_de_callback, update_de_texto

pytestmark = pytest.mark.contraria


def _profissional(db, email: str) -> Professional:
    registro = Professional(
        full_name='Dra. Contrária', email=email, password_hash='x', role='medico', profession='Médica'
    )
    db.add(registro)
    db.commit()
    return registro


async def test_ct_bot_x01_confirmar_o_lembrete_de_outra_pessoa(fabrica_de_sessao, db):
    """CT-BOT-X01 · o bot NÃO deveria deixar alguém registrar a dose de outra pessoa."""
    dona = cenarios.usuario(db, novo_usuario_telegram())
    remedio = cenarios.medicamento(db, dona)
    lembrete = cenarios.lembrete(db, remedio, status='delivered')

    intrusa = novo_usuario_telegram()
    toque = update_de_callback(intrusa, f'confirm:{lembrete.id}')
    await reminder_handlers.confirm_callback(toque, ContextoFalso())

    assert 'não encontrado' in ' '.join(alertas(toque)).lower()
    db.refresh(lembrete)
    assert lembrete.status == 'delivered'  # nada foi registrado no lembrete alheio


async def test_ct_bot_x02_marcar_nao_tomado_no_lembrete_de_outra_pessoa(fabrica_de_sessao, db):
    """CT-BOT-X02 · mesma proteção no caminho do "não tomei"."""
    dona = cenarios.usuario(db, novo_usuario_telegram())
    remedio = cenarios.medicamento(db, dona)
    lembrete = cenarios.lembrete(db, remedio, status='delivered')

    toque = update_de_callback(novo_usuario_telegram(), f'not_taken:{lembrete.id}')
    await reminder_handlers.not_taken_callback(toque, ContextoFalso())

    assert 'não encontrado' in ' '.join(alertas(toque)).lower()
    db.refresh(lembrete)
    assert lembrete.status == 'delivered'


async def test_ct_bot_x03_adiar_o_lembrete_de_outra_pessoa(fabrica_de_sessao, db):
    """CT-BOT-X03 · e no caminho do adiamento."""
    dona = cenarios.usuario(db, novo_usuario_telegram())
    remedio = cenarios.medicamento(db, dona)
    lembrete = cenarios.lembrete(db, remedio, status='delivered')

    toque = update_de_callback(novo_usuario_telegram(), f'snooze:{lembrete.id}:30')
    await reminder_handlers.snooze_callback(toque, ContextoFalso())

    assert 'não encontrado' in ' '.join(alertas(toque)).lower()
    db.refresh(lembrete)
    assert lembrete.snooze_count == 0


async def test_ct_bot_x04_confirmar_um_lembrete_que_nunca_existiu(fabrica_de_sessao, db):
    """CT-BOT-X04 · heurística "nome inexistente": id que não existe não pode quebrar o bot."""
    pessoa = cenarios.usuario(db, novo_usuario_telegram())

    toque = update_de_callback(pessoa.telegram_user_id, 'confirm:999999')
    await reminder_handlers.confirm_callback(toque, ContextoFalso())

    assert 'não encontrado' in ' '.join(alertas(toque)).lower()


async def test_ct_bot_x05_start_com_convite_inventado(fabrica_de_sessao, db):
    """CT-BOT-X05 · token de convite que ninguém emitiu."""
    update = update_de_texto(novo_usuario_telegram(), '/start token-inventado')

    await start_handlers.start(update, ContextoFalso(args=['token-inventado']))

    mensagens = ' '.join(respostas(update))
    assert 'não é válido' in mensagens or 'expirou' in mensagens
    # E o bot segue utilizável: a boas-vindas vem em seguida, não um silêncio.
    assert 'Hora do Remédio' in mensagens


async def test_ct_bot_x06_usar_o_mesmo_convite_duas_vezes(fabrica_de_sessao, db):
    """CT-BOT-X06 · heurística "nome já existente"/uso único: convite não se reaproveita."""
    profissional = _profissional(db, 'convite.duplo@example.com')
    paciente = patient_service.create_patient(
        db, profissional, full_name='Paciente do Convite', internal_identifier='BOT-CONV-001'
    )
    convite, token = patient_service.create_invite(db, profissional, paciente)

    primeira = novo_usuario_telegram()
    aceite = update_de_callback(primeira, f'patient_invite:confirm:{convite.id}')
    await patient_handlers.confirm_callback(aceite, ContextoFalso())

    db.refresh(paciente)
    assert paciente.telegram_link_status == 'linked'

    # Outra pessoa tenta usar o mesmo convite depois
    segunda = novo_usuario_telegram()
    repetido = update_de_texto(segunda, f'/start {token}')
    await start_handlers.start(repetido, ContextoFalso(args=[token]))

    mensagens = ' '.join(respostas(repetido))
    assert 'não é válido' in mensagens or 'já foi usado' in mensagens or 'expirou' in mensagens

    db.refresh(paciente)
    assert paciente.user_id is not None


async def test_ct_bot_x07_recusar_o_convite_nao_vincula_ninguem(fabrica_de_sessao, db):
    """CT-BOT-X07 · o "não sou eu" precisa funcionar: é a proteção de quem recebeu o link errado."""
    profissional = _profissional(db, 'convite.recusa@example.com')
    paciente = patient_service.create_patient(
        db, profissional, full_name='Paciente que Recusa', internal_identifier='BOT-CONV-002'
    )
    convite, _token = patient_service.create_invite(db, profissional, paciente)

    recusa = update_de_callback(novo_usuario_telegram(), f'patient_invite:cancel:{convite.id}')
    await patient_handlers.cancel_callback(recusa, ContextoFalso())

    db.refresh(paciente)
    assert paciente.telegram_link_status != 'linked'
    assert db.get(Patient, paciente.id).user_id is None
