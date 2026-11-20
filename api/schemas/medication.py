from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.schemas.schedule import ScheduleCreate, ScheduleOut


class MedicationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    dosage: str = Field(min_length=1, max_length=100)
    quantity: str = Field(min_length=1, max_length=100)
    instructions: str | None = Field(default=None, max_length=500)
    audio_text: str | None = Field(
        default=None, max_length=500, description="Descrição opcional falada (TTS) no lembrete (RF02)"
    )
    photo_path: str | None = Field(default=None, description="Caminho local da fotografia da embalagem (RF03)")
    start_date: date
    end_date: date | None = None
    schedules: list[ScheduleCreate] = Field(min_length=1, description="Ao menos um horário é obrigatório (RN02)")

    @model_validator(mode="after")
    def _validar_datas(self) -> "MedicationCreate":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date não pode ser anterior a start_date")
        return self


class MedicationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    dosage: str | None = Field(default=None, min_length=1, max_length=100)
    quantity: str | None = Field(default=None, min_length=1, max_length=100)
    instructions: str | None = Field(default=None, max_length=500)
    audio_text: str | None = Field(default=None, max_length=500)
    start_date: date | None = None
    end_date: date | None = None
    active: bool | None = None
    photo_path: str | None = None
    schedules: list[ScheduleCreate] | None = Field(
        default=None, description="Quando enviado, substitui todos os horários existentes (CT10)"
    )


class MedicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    dosage: str
    quantity: str
    instructions: str | None
    audio_text: str | None
    photo_path: str | None
    start_date: date
    end_date: date | None
    active: bool
    schedules: list[ScheduleOut] = []
