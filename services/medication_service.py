from sqlalchemy.orm import Session

from api.schemas.medication import MedicationCreate, MedicationUpdate
from api.schemas.schedule import ScheduleCreate
from database.models import Medication, Schedule, User


def get_or_create_user(db: Session, telegram_user_id: int, timezone: str = "America/Sao_Paulo") -> User:
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
    if user is None:
        user = User(telegram_user_id=telegram_user_id, timezone=timezone)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def build_schedules(schedule_items: list[ScheduleCreate], user: User) -> list[Schedule]:
    return [
        Schedule(
            recurrence_type=item.recurrence_type,
            schedule_time=item.schedule_time,
            interval_hours=item.interval_hours,
            weekdays=item.weekdays,
            timezone=item.timezone or user.timezone,
        )
        for item in schedule_items
    ]


def list_medications(db: Session, user: User, active: bool | None = None) -> list[Medication]:
    query = db.query(Medication).filter(Medication.user_id == user.id)
    if active is not None:
        query = query.filter(Medication.active == active)
    return query.order_by(Medication.name).all()


def create_medication(db: Session, user: User, payload: MedicationCreate) -> Medication:
    medication = Medication(
        user_id=user.id,
        name=payload.name,
        dosage=payload.dosage,
        quantity=payload.quantity,
        instructions=payload.instructions,
        audio_text=payload.audio_text,
        photo_path=payload.photo_path,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    medication.schedules = build_schedules(payload.schedules, user)
    db.add(medication)
    db.commit()
    db.refresh(medication)
    return medication


def update_medication(db: Session, medication: Medication, user: User, payload: MedicationUpdate) -> Medication:
    updates = payload.model_dump(exclude_unset=True, exclude={"schedules"})
    for field, value in updates.items():
        setattr(medication, field, value)

    if payload.schedules is not None:
        medication.schedules = build_schedules(payload.schedules, user)

    db.commit()
    db.refresh(medication)
    return medication


def delete_medication(db: Session, medication: Medication) -> None:
    db.delete(medication)
    db.commit()
