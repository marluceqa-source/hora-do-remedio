"""Planos de tratamento e medicamentos cadastrados pelo profissional (RF05, RF06, RF07).

Reaproveita deliberadamente `Medication`/`Schedule` (já consumidos pelo bot/scheduler): ativar
um `TreatmentMedication` materializa (cria ou atualiza) a linha correspondente dessas tabelas
— nenhum agendador novo é construído aqui."""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from api.schemas.schedule import ScheduleCreate
from database.models import (
    Medication,
    Patient,
    Professional,
    Schedule,
    TreatmentMedication,
    TreatmentMedicationSchedule,
    TreatmentPlan,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TreatmentServiceError(Exception):
    """Erro genérico de planos/medicamentos de tratamento."""


class PatientNotLinkedError(TreatmentServiceError):
    """RF06: só é possível ativar (e notificar) quando o paciente já está vinculado ao Telegram."""


class InvalidStatusTransitionError(TreatmentServiceError):
    pass


class InsufficientRoleError(TreatmentServiceError):
    """RN20: a ativação clínica respeita as atribuições do profissional."""


_ACTIVATION_ALLOWED_ROLES = ("medico",)


def _build_treatment_schedules(schedule_items: list[ScheduleCreate]) -> list[TreatmentMedicationSchedule]:
    return [
        TreatmentMedicationSchedule(
            recurrence_type=item.recurrence_type,
            schedule_time=item.schedule_time,
            interval_hours=item.interval_hours,
            weekdays=item.weekdays,
            timezone=item.timezone or "America/Sao_Paulo",
        )
        for item in schedule_items
    ]


def _build_medication_schedules(treatment_schedules: list[TreatmentMedicationSchedule]) -> list[Schedule]:
    return [
        Schedule(
            recurrence_type=s.recurrence_type,
            schedule_time=s.schedule_time,
            interval_hours=s.interval_hours,
            weekdays=s.weekdays,
            timezone=s.timezone,
        )
        for s in treatment_schedules
    ]


def create_treatment_medication(
    db: Session,
    professional: Professional,
    patient: Patient,
    *,
    medication_name: str,
    dosage: str,
    quantity_per_administration: str,
    start_date: date,
    schedules: list[ScheduleCreate],
    active_ingredient: str | None = None,
    presentation: str | None = None,
    route: str | None = None,
    dosage_unit: str | None = None,
    frequency_description: str | None = None,
    instructions: str | None = None,
    end_date: date | None = None,
    photo_path: str | None = None,
) -> TreatmentMedication:
    plan = TreatmentPlan(patient_id=patient.id, professional_id=professional.id, status="draft")
    db.add(plan)
    db.flush()

    treatment_medication = TreatmentMedication(
        treatment_plan_id=plan.id,
        medication_name=medication_name,
        active_ingredient=active_ingredient,
        presentation=presentation,
        route=route,
        dosage=dosage,
        dosage_unit=dosage_unit,
        quantity_per_administration=quantity_per_administration,
        frequency_description=frequency_description,
        instructions=instructions,
        start_date=start_date,
        end_date=end_date,
        photo_path=photo_path,
        status="draft",
    )
    treatment_medication.schedules = _build_treatment_schedules(schedules)
    db.add(treatment_medication)
    db.commit()
    db.refresh(treatment_medication)
    return treatment_medication


def list_treatment_medications(db: Session, patient: Patient) -> list[TreatmentMedication]:
    return (
        db.query(TreatmentMedication)
        .join(TreatmentPlan, TreatmentPlan.id == TreatmentMedication.treatment_plan_id)
        .filter(TreatmentPlan.patient_id == patient.id)
        .order_by(TreatmentMedication.created_at.desc())
        .all()
    )


def get_treatment_medication_for_patient(db: Session, patient: Patient, treatment_medication_id: int) -> TreatmentMedication | None:
    return (
        db.query(TreatmentMedication)
        .join(TreatmentPlan, TreatmentPlan.id == TreatmentMedication.treatment_plan_id)
        .filter(TreatmentPlan.patient_id == patient.id, TreatmentMedication.id == treatment_medication_id)
        .first()
    )


_EDITABLE_FIELDS = (
    "medication_name",
    "active_ingredient",
    "presentation",
    "route",
    "dosage",
    "dosage_unit",
    "quantity_per_administration",
    "frequency_description",
    "instructions",
    "start_date",
    "end_date",
    "photo_path",
)


def update_treatment_medication(
    db: Session,
    treatment_medication: TreatmentMedication,
    *,
    fields: dict,
    schedules: list[ScheduleCreate] | None,
) -> TreatmentMedication:
    if treatment_medication.status not in ("draft", "active"):
        raise InvalidStatusTransitionError("Só é possível editar tratamentos em rascunho ou ativos")

    target = treatment_medication
    if treatment_medication.status == "active":
        # RN27: tratamento ativo -> nova versão em rascunho; a versão ativa atual continua
        # valendo (e gerando lembretes) até esta nova versão ser ativada explicitamente.
        target = TreatmentMedication(
            treatment_plan_id=treatment_medication.treatment_plan_id,
            previous_version_id=treatment_medication.id,
            status="draft",
            **{field: getattr(treatment_medication, field) for field in _EDITABLE_FIELDS},
        )
        if schedules is None:
            target.schedules = _build_treatment_schedules(
                [
                    ScheduleCreate(
                        recurrence_type=s.recurrence_type,
                        schedule_time=s.schedule_time,
                        interval_hours=s.interval_hours,
                        weekdays=s.weekdays,
                        timezone=s.timezone,
                    )
                    for s in treatment_medication.schedules
                ]
            )
        db.add(target)

    for field, value in fields.items():
        setattr(target, field, value)
    if schedules is not None:
        target.schedules = _build_treatment_schedules(schedules)

    db.commit()
    db.refresh(target)
    return target


def activate_treatment_medication(
    db: Session, professional: Professional, treatment_medication: TreatmentMedication
) -> TreatmentMedication:
    if professional.role not in _ACTIVATION_ALLOWED_ROLES:
        raise InsufficientRoleError()
    if treatment_medication.status not in ("draft",):
        raise InvalidStatusTransitionError("Só é possível ativar um tratamento em rascunho")

    plan = treatment_medication.treatment_plan
    patient = plan.patient
    if patient.user_id is None:
        raise PatientNotLinkedError()

    existing_medication_id = None
    if treatment_medication.previous_version_id:
        previous = db.get(TreatmentMedication, treatment_medication.previous_version_id)
        if previous is not None and previous.linked_medication_id is not None:
            existing_medication_id = previous.linked_medication_id
            previous.status = "closed"
            # A titularidade do Medication passa para esta nova versão — sem isso, a
            # constraint única de linked_medication_id rejeitaria a nova linha (RN27).
            previous.linked_medication_id = None

    audio_text = f"{treatment_medication.medication_name}, {treatment_medication.dosage}"
    if treatment_medication.dosage_unit:
        audio_text += f" {treatment_medication.dosage_unit}"
    audio_text += f". {treatment_medication.quantity_per_administration}."
    if treatment_medication.instructions:
        audio_text += f" {treatment_medication.instructions}"

    if existing_medication_id is not None:
        medication = db.get(Medication, existing_medication_id)
        medication.name = treatment_medication.medication_name
        medication.dosage = treatment_medication.dosage + (f" {treatment_medication.dosage_unit}" if treatment_medication.dosage_unit else "")
        medication.quantity = treatment_medication.quantity_per_administration
        medication.instructions = treatment_medication.instructions
        medication.audio_text = audio_text
        medication.photo_path = treatment_medication.photo_path
        medication.start_date = treatment_medication.start_date
        medication.end_date = treatment_medication.end_date
        medication.active = True
        # RF07 ponto 4-5: substitui os horários — reflete só nos agendamentos futuros; os
        # ReminderEvents (histórico) já emitidos continuam intactos (RN27), pois pertencem
        # ao mesmo medication_id, nunca apagado.
        medication.schedules = _build_medication_schedules(treatment_medication.schedules)
    else:
        medication = Medication(
            user_id=patient.user_id,
            name=treatment_medication.medication_name,
            dosage=treatment_medication.dosage + (f" {treatment_medication.dosage_unit}" if treatment_medication.dosage_unit else ""),
            quantity=treatment_medication.quantity_per_administration,
            instructions=treatment_medication.instructions,
            audio_text=audio_text,
            photo_path=treatment_medication.photo_path,
            start_date=treatment_medication.start_date,
            end_date=treatment_medication.end_date,
            active=True,
        )
        medication.schedules = _build_medication_schedules(treatment_medication.schedules)
        db.add(medication)
        db.flush()

    treatment_medication.linked_medication_id = medication.id
    treatment_medication.status = "active"
    plan.status = "active"
    plan.activated_at = _utcnow()
    db.commit()
    db.refresh(treatment_medication)
    return treatment_medication


def suspend_treatment_medication(db: Session, treatment_medication: TreatmentMedication) -> TreatmentMedication:
    if treatment_medication.status != "active":
        raise InvalidStatusTransitionError("Só é possível suspender um tratamento ativo")

    treatment_medication.status = "suspended"
    if treatment_medication.linked_medication_id is not None:
        medication = db.get(Medication, treatment_medication.linked_medication_id)
        if medication is not None:
            # RN28: medicamento inativo não gera novos lembretes (o scheduler já respeita isso).
            medication.active = False

    db.commit()
    db.refresh(treatment_medication)
    return treatment_medication


def get_version_chain(db: Session, treatment_medication: TreatmentMedication) -> list[TreatmentMedication]:
    """RF07: "Consultar versões anteriores" — da mais antiga para a mais recente."""
    chain = [treatment_medication]
    current = treatment_medication
    while current.previous_version_id is not None:
        current = db.get(TreatmentMedication, current.previous_version_id)
        if current is None:
            break
        chain.append(current)
    return list(reversed(chain))
