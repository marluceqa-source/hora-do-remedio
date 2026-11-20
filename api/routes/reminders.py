from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.schemas.reminder import ReminderEventOut, ReminderSnoozeRequest
from database.models import ReminderEvent, User
from services import reminder_service

router = APIRouter(prefix="/api/v1/reminders", tags=["Lembretes"])


def _get_owned_reminder(db: Session, reminder_id: int, user: User) -> ReminderEvent:
    reminder = reminder_service.get_owned_reminder(db, reminder_id, user)
    if reminder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lembrete não encontrado")
    return reminder


@router.get("/today", response_model=list[ReminderEventOut], summary="Consulta os lembretes de hoje (RF09)")
def reminders_today(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ReminderEvent]:
    return reminder_service.list_today(db, user)


@router.post(
    "/{reminder_id}/confirm",
    response_model=ReminderEventOut,
    summary="Confirma a administração de uma dose (RF07, RN04)",
)
def confirm_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReminderEvent:
    reminder = _get_owned_reminder(db, reminder_id, user)
    try:
        return reminder_service.confirm(db, reminder)
    except reminder_service.ReminderAlreadyConfirmedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta dose já foi confirmada anteriormente (RN05)",
        ) from exc


@router.post(
    "/{reminder_id}/snooze",
    response_model=ReminderEventOut,
    summary="Adia um lembrete sem alterar o horário original (RF08, RN06)",
)
def snooze_reminder(
    reminder_id: int,
    payload: ReminderSnoozeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReminderEvent:
    reminder = _get_owned_reminder(db, reminder_id, user)
    try:
        return reminder_service.snooze(db, reminder)
    except reminder_service.ReminderAlreadyConfirmedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta dose já foi confirmada") from exc
