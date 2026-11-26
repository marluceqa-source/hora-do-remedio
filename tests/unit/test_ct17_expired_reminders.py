"""CT17 — botões antigos ou expirados (card #35).

O status `expired` existia no modelo, nos relatórios e no rótulo do bot, mas nenhum código o
atribuía. Estes testes cobrem a transição e, principalmente, a garantia que ela **não** pode
quebrar: expirado é "não sabemos", nunca "não tomou" (RN12 / RN29).
"""

from datetime import date, datetime, timedelta

import pytest

from core.config import get_settings
from database.models import Medication, ReminderEvent, User
from services import reminder_service


# Relógio de referência fixo. Os testes passam `now=_AGORA` para a função, de modo que o
# resultado não dependa do fuso nem do relógio da máquina que roda a suíte.
_AGORA = datetime(2026, 11, 26, 12, 0, 0)


def _seed(db_session, telegram_user_id: int, *, status: str, horas_atras: float) -> ReminderEvent:
    user = User(telegram_user_id=telegram_user_id, timezone="America/Sao_Paulo")
    db_session.add(user)
    db_session.flush()

    medication = Medication(
        user_id=user.id,
        name="Losartana",
        dosage="50mg",
        quantity="1 comprimido",
        start_date=date.today(),
    )
    db_session.add(medication)
    db_session.flush()

    reminder = ReminderEvent(
        medication_id=medication.id,
        scheduled_datetime=_AGORA - timedelta(hours=horas_atras),
        status=status,
    )
    db_session.add(reminder)
    db_session.commit()
    db_session.refresh(reminder)
    return reminder


def _janela() -> int:
    return get_settings().reminder_expire_hours


# --- A transição -----------------------------------------------------------------------


@pytest.mark.parametrize("status", ["pending", "delivered", "snoozed"])
def test_ct17_expira_lembrete_sem_resposta_alem_da_janela(db_session, status):
    reminder = _seed(db_session, 900, status=status, horas_atras=_janela() + 1)

    assert reminder_service.expire_stale_reminders(db_session, now=_AGORA) == 1

    db_session.refresh(reminder)
    assert reminder.status == "expired"


@pytest.mark.parametrize("status", ["pending", "delivered", "snoozed"])
def test_ct17_nao_expira_dentro_da_janela(db_session, status):
    reminder = _seed(db_session, 901, status=status, horas_atras=_janela() - 1)

    assert reminder_service.expire_stale_reminders(db_session, now=_AGORA) == 0

    db_session.refresh(reminder)
    assert reminder.status == status


@pytest.mark.parametrize("status", ["confirmed", "not_taken"])
def test_ct17_nao_toca_em_dose_ja_declarada(db_session, status):
    """Confirmada ou marcada como não tomada já tem a declaração da pessoa: expirar apagaria isso."""
    reminder = _seed(db_session, 902, status=status, horas_atras=_janela() * 10)

    assert reminder_service.expire_stale_reminders(db_session, now=_AGORA) == 0

    db_session.refresh(reminder)
    assert reminder.status == status


def test_ct17_expirar_e_idempotente(db_session):
    reminder = _seed(db_session, 903, status="delivered", horas_atras=_janela() + 1)

    assert reminder_service.expire_stale_reminders(db_session, now=_AGORA) == 1
    assert reminder_service.expire_stale_reminders(db_session, now=_AGORA) == 0

    db_session.refresh(reminder)
    assert reminder.status == "expired"


def test_ct17_borda_exata_da_janela(db_session):
    """Exatamente na janela ainda não expira; um minuto além, sim."""
    reminder = _seed(db_session, 904, status="delivered", horas_atras=_janela())

    assert reminder_service.expire_stale_reminders(db_session, now=_AGORA) == 0

    futuro = _AGORA + timedelta(minutes=1)

    assert reminder_service.expire_stale_reminders(db_session, now=futuro) == 1

    db_session.refresh(reminder)
    assert reminder.status == "expired"


# --- RN12 / RN29: expirado não é "não tomou" -------------------------------------------


def test_ct17_expirado_nunca_vira_not_taken(db_session):
    """A garantia central: a passagem do tempo não produz um fato clínico."""
    reminder = _seed(db_session, 905, status="delivered", horas_atras=_janela() * 5)

    reminder_service.expire_stale_reminders(db_session, now=_AGORA)

    db_session.refresh(reminder)
    assert reminder.status == "expired"
    assert reminder.status != "not_taken"


def test_ct17_expirado_conta_como_sem_confirmacao_e_nao_como_nao_tomada(db_session):
    from services import report_service

    reminder = _seed(db_session, 906, status="delivered", horas_atras=_janela() + 1)
    reminder_service.expire_stale_reminders(db_session, now=_AGORA)
    db_session.refresh(reminder)

    assert "expired" in report_service._UNCONFIRMED_STATUSES
    assert reminder.status in report_service._UNCONFIRMED_STATUSES


# --- Botão antigo: a resposta é recusada ------------------------------------------------


def test_ct17_confirmar_lembrete_expirado_e_recusado(db_session):
    reminder = _seed(db_session, 907, status="expired", horas_atras=_janela() + 1)

    with pytest.raises(reminder_service.ReminderExpiredError):
        reminder_service.confirm(db_session, reminder)

    db_session.refresh(reminder)
    assert reminder.status == "expired"
    assert reminder.confirmed_datetime is None


def test_ct17_adiar_lembrete_expirado_e_recusado(db_session):
    reminder = _seed(db_session, 908, status="expired", horas_atras=_janela() + 1)

    with pytest.raises(reminder_service.ReminderExpiredError):
        reminder_service.snooze(db_session, reminder)

    db_session.refresh(reminder)
    assert reminder.status == "expired"
    assert reminder.snooze_count == 0


def test_ct17_marcar_nao_tomado_em_expirado_e_recusado(db_session):
    """Mesmo "não tomei" é recusado: um toque acidental num botão antigo não vira registro."""
    reminder = _seed(db_session, 909, status="expired", horas_atras=_janela() + 1)

    with pytest.raises(reminder_service.ReminderExpiredError):
        reminder_service.mark_not_taken(db_session, reminder)

    db_session.refresh(reminder)
    assert reminder.status == "expired"


def test_ct17_lembrete_recente_continua_respondivel(db_session):
    """A recusa é da expiração, não do tempo decorrido: dentro da janela tudo funciona."""
    reminder = _seed(db_session, 910, status="delivered", horas_atras=_janela() - 1)

    confirmado = reminder_service.confirm(db_session, reminder)

    assert confirmado.status == "confirmed"
    assert confirmado.confirmed_datetime is not None
