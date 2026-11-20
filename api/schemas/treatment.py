from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.schemas.schedule import ScheduleCreate


class TreatmentScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    treatment_medication_id: int
    recurrence_type: str
    schedule_time: time | None
    interval_hours: int | None
    weekdays: str | None
    timezone: str


class TreatmentMedicationCreateRequest(BaseModel):
    medication_name: str = Field(min_length=1, max_length=200)
    active_ingredient: str | None = Field(default=None, max_length=200)
    presentation: str | None = Field(default=None, max_length=100)
    route: str | None = Field(default=None, max_length=100)
    dosage: str = Field(min_length=1, max_length=100)
    dosage_unit: str | None = Field(default=None, max_length=50)
    quantity_per_administration: str = Field(min_length=1, max_length=100)
    frequency_description: str | None = Field(default=None, max_length=200)
    instructions: str | None = Field(default=None, max_length=500)
    start_date: date
    end_date: date | None = None
    photo_path: str | None = Field(default=None, max_length=300)
    schedules: list[ScheduleCreate] = Field(min_length=1, description="Ao menos um horário é obrigatório")

    @model_validator(mode="after")
    def _validar_datas(self) -> "TreatmentMedicationCreateRequest":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date não pode ser anterior a start_date")
        return self


class TreatmentMedicationUpdateRequest(BaseModel):
    medication_name: str | None = Field(default=None, min_length=1, max_length=200)
    active_ingredient: str | None = Field(default=None, max_length=200)
    presentation: str | None = Field(default=None, max_length=100)
    route: str | None = Field(default=None, max_length=100)
    dosage: str | None = Field(default=None, min_length=1, max_length=100)
    dosage_unit: str | None = Field(default=None, max_length=50)
    quantity_per_administration: str | None = Field(default=None, min_length=1, max_length=100)
    frequency_description: str | None = Field(default=None, max_length=200)
    instructions: str | None = Field(default=None, max_length=500)
    start_date: date | None = None
    end_date: date | None = None
    photo_path: str | None = None
    schedules: list[ScheduleCreate] | None = Field(
        default=None, description="Quando enviado, substitui todos os horários (RF07)"
    )


class TreatmentMedicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    treatment_plan_id: int
    medication_name: str
    active_ingredient: str | None
    presentation: str | None
    route: str | None
    dosage: str
    dosage_unit: str | None
    quantity_per_administration: str
    frequency_description: str | None
    instructions: str | None
    start_date: date
    end_date: date | None
    status: str
    photo_path: str | None
    linked_medication_id: int | None
    previous_version_id: int | None
    created_at: datetime
    updated_at: datetime
    schedules: list[TreatmentScheduleOut] = []
