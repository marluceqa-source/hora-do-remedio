from datetime import date, datetime, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from core.config import get_settings
from database.models import Medication, ReminderEvent, User


class ReminderAlreadyConfirmedError(Exception):
    """Levantada ao tentar confirmar, adiar ou marcar como não tomada uma dose já confirmada (RN05)."""


class ReminderExpiredError(Exception):
    """Levantada ao responder um lembrete já expirado (CT17 — botões antigos ou expirados)."""


# Status de um lembrete que ainda aguarda resposta: são estes que podem expirar.
_AWAITING_RESPONSE_STATUSES = ("pending", "delivered", "snoozed")


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _now_in_app_timezone() -> datetime:
    """Mesmo relógio com que `SchedulerService._fire` grava `scheduled_datetime`."""
    return datetime.now(ZoneInfo(get_settings().timezone)).replace(tzinfo=None)


def list_today(db: Session, user: User) -> list[ReminderEvent]:
    today = datetime.now(ZoneInfo(user.timezone)).date()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())
    return (
        db.query(ReminderEvent)
        .join(Medication)
        .filter(Medication.user_id == user.id)
        .filter(ReminderEvent.scheduled_datetime >= start)
        .filter(ReminderEvent.scheduled_datetime <= end)
        .order_by(ReminderEvent.scheduled_datetime)
        .all()
    )


def _period_bounds(period: Literal["day", "week", "month"], reference: date) -> tuple[date, date]:
    if period == "day":
        return reference, reference + timedelta(days=1)
    if period == "week":
        start = reference - timedelta(days=reference.weekday())
        return start, start + timedelta(days=7)
    start = reference.replace(day=1)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, next_month


def get_history(
    db: Session,
    user: User,
    period: Literal["day", "week", "month"] = "day",
    reference_date: date | None = None,
) -> list[ReminderEvent]:
    ref = reference_date or datetime.now(ZoneInfo(user.timezone)).date()
    start, end = _period_bounds(period, ref)
    return (
        db.query(ReminderEvent)
        .join(Medication)
        .filter(Medication.user_id == user.id)
        .filter(ReminderEvent.scheduled_datetime >= datetime.combine(start, datetime.min.time()))
        .filter(ReminderEvent.scheduled_datetime < datetime.combine(end, datetime.min.time()))
        .order_by(ReminderEvent.scheduled_datetime)
        .all()
    )


def get_owned_reminder(db: Session, reminder_id: int, user: User) -> ReminderEvent | None:
    reminder = db.get(ReminderEvent, reminder_id)
    if reminder is None or reminder.medication.user_id != user.id:
        return None
    return reminder


def expire_stale_reminders(db: Session, *, now: datetime | None = None) -> int:
    """Marca como `expired` os lembretes sem resposta além da janela (CT17). Devolve quantos.

    **`expired` não é `not_taken`** (RN12/RN29). Esta transição registra que a janela de
    resposta fechou sem resposta — nunca que a pessoa deixou de tomar o medicamento. Por isso
    os relatórios e o painel contam `expired` junto dos "sem confirmação", e não das doses não
    tomadas.

    Só alcança quem ainda aguardava resposta: uma dose confirmada ou explicitamente marcada
    como não tomada já tem a declaração da pessoa e não é tocada aqui.

    O relógio usado é o do **fuso da aplicação**, não UTC, porque `scheduled_datetime` é
    gravado por `SchedulerService._fire` no fuso local do agendamento
    (`datetime.now(tz).replace(tzinfo=None)`). Comparar com UTC expiraria os lembretes com
    uma diferença igual ao deslocamento do fuso — três horas mais cedo em São Paulo.

    Limitação: usuários em fusos diferentes do fuso da aplicação têm a janela deslocada pela
    diferença entre os dois. `ReminderEvent` não guarda o `Schedule` que o originou, então não
    há como recuperar o fuso exato de cada lembrete sem mudar o modelo.
    """
    momento = now or _now_in_app_timezone()
    limite = momento - timedelta(hours=get_settings().reminder_expire_hours)
    atingidos = (
        db.query(ReminderEvent)
        .filter(
            ReminderEvent.status.in_(_AWAITING_RESPONSE_STATUSES),
            ReminderEvent.scheduled_datetime < limite,
        )
        .all()
    )
    for reminder in atingidos:
        reminder.status = "expired"
    if atingidos:
        db.commit()
    return len(atingidos)


def _reject_if_unanswerable(reminder: ReminderEvent) -> None:
    if reminder.status == "confirmed":
        raise ReminderAlreadyConfirmedError()
    if reminder.status == "expired":
        raise ReminderExpiredError()


def confirm(db: Session, reminder: ReminderEvent) -> ReminderEvent:
    _reject_if_unanswerable(reminder)
    reminder.status = "confirmed"
    reminder.confirmed_datetime = _utcnow_naive()
    db.commit()
    db.refresh(reminder)
    return reminder


def snooze(db: Session, reminder: ReminderEvent) -> ReminderEvent:
    _reject_if_unanswerable(reminder)
    reminder.status = "snoozed"
    reminder.snooze_count += 1
    db.commit()
    db.refresh(reminder)
    return reminder


def mark_not_taken(db: Session, reminder: ReminderEvent) -> ReminderEvent:
    _reject_if_unanswerable(reminder)
    reminder.status = "not_taken"
    db.commit()
    db.refresh(reminder)
    return reminder
