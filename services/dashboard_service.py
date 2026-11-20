"""Painel operacional do profissional (RF02).

Os números refletem confirmações declaradas e entregas registradas — nunca uma prova de que
o paciente efetivamente tomou o medicamento (RN12); é por isso que "doses sem confirmação" é
contado à parte de "doses não tomadas" (status explícito `not_taken`).
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from database.models import Medication, Professional, ReminderEvent, TreatmentMedication, TreatmentPlan
from services import patient_service

_UNCONFIRMED_STATUSES = ("pending", "delivered", "snoozed", "expired")
_TREATMENT_ENDING_SOON_DAYS = 7


def compute_dashboard(
    db: Session,
    professional: Professional,
    *,
    patient_id: int | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    patients = patient_service.list_authorized_patients(db, professional)
    if patient_id is not None:
        patients = [p for p in patients if p.id == patient_id]

    patient_ids = [p.id for p in patients]
    user_ids = [p.user_id for p in patients if p.user_id is not None]

    # `in_([-1])` quando a lista está vazia evita sintaxe especial para "nenhum resultado".
    treatment_query = (
        db.query(TreatmentMedication)
        .join(TreatmentPlan, TreatmentPlan.id == TreatmentMedication.treatment_plan_id)
        .filter(TreatmentPlan.patient_id.in_(patient_ids or [-1]))
    )
    if status:
        treatment_query = treatment_query.filter(TreatmentMedication.status == status)

    active_treatments = treatment_query.filter(TreatmentMedication.status == "active").count()

    today = date.today()
    soon_cutoff = today + timedelta(days=_TREATMENT_ENDING_SOON_DAYS)
    treatments_ending_soon = treatment_query.filter(
        TreatmentMedication.status == "active",
        TreatmentMedication.end_date.isnot(None),
        TreatmentMedication.end_date >= today,
        TreatmentMedication.end_date <= soon_cutoff,
    ).count()

    reminder_query = (
        db.query(ReminderEvent)
        .join(Medication, Medication.id == ReminderEvent.medication_id)
        .filter(Medication.user_id.in_(user_ids or [-1]))
    )
    if start_date is not None:
        reminder_query = reminder_query.filter(ReminderEvent.scheduled_datetime >= datetime.combine(start_date, time.min))
    if end_date is not None:
        reminder_query = reminder_query.filter(
            ReminderEvent.scheduled_datetime < datetime.combine(end_date + timedelta(days=1), time.min)
        )

    return {
        "total_patients": len(patients),
        "active_treatments": active_treatments,
        "treatments_ending_soon": treatments_ending_soon,
        "reminders_sent": reminder_query.filter(ReminderEvent.delivery_datetime.isnot(None)).count(),
        "doses_confirmed": reminder_query.filter(ReminderEvent.status == "confirmed").count(),
        "doses_not_taken": reminder_query.filter(ReminderEvent.status == "not_taken").count(),
        "doses_unconfirmed": reminder_query.filter(ReminderEvent.status.in_(_UNCONFIRMED_STATUSES)).count(),
    }
