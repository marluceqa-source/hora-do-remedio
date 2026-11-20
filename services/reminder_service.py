from datetime import date, datetime, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from database.models import Medication, ReminderEvent, User


class ReminderAlreadyConfirmedError(Exception):
    """Levantada ao tentar confirmar, adiar ou marcar como não tomada uma dose já confirmada (RN05)."""


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


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


def confirm(db: Session, reminder: ReminderEvent) -> ReminderEvent:
    if reminder.status == "confirmed":
        raise ReminderAlreadyConfirmedError()
    reminder.status = "confirmed"
    reminder.confirmed_datetime = _utcnow_naive()
    db.commit()
    db.refresh(reminder)
    return reminder


def snooze(db: Session, reminder: ReminderEvent) -> ReminderEvent:
    if reminder.status == "confirmed":
        raise ReminderAlreadyConfirmedError()
    reminder.status = "snoozed"
    reminder.snooze_count += 1
    db.commit()
    db.refresh(reminder)
    return reminder


def mark_not_taken(db: Session, reminder: ReminderEvent) -> ReminderEvent:
    if reminder.status == "confirmed":
        raise ReminderAlreadyConfirmedError()
    reminder.status = "not_taken"
    db.commit()
    db.refresh(reminder)
    return reminder
