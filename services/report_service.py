from sqlalchemy.orm import Session

from database.models import Medication, ReminderEvent, User

_UNCONFIRMED_STATUSES = ("pending", "delivered", "snoozed", "expired")


def compute_report(db: Session, user: User) -> dict:
    base_query = db.query(ReminderEvent).join(Medication).filter(Medication.user_id == user.id)
    total_scheduled = base_query.count()
    total_confirmed = base_query.filter(ReminderEvent.status == "confirmed").count()
    total_not_taken = base_query.filter(ReminderEvent.status == "not_taken").count()
    total_unconfirmed = base_query.filter(ReminderEvent.status.in_(_UNCONFIRMED_STATUSES)).count()
    confirmation_rate = round((total_confirmed / total_scheduled * 100), 2) if total_scheduled else 0.0
    return {
        "total_scheduled": total_scheduled,
        "total_confirmed": total_confirmed,
        "total_not_taken": total_not_taken,
        "total_unconfirmed": total_unconfirmed,
        "confirmation_rate": confirmation_rate,
    }
