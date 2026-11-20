from datetime import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RecurrenceType = Literal["daily", "weekly", "interval"]


class ScheduleCreate(BaseModel):
    recurrence_type: RecurrenceType
    schedule_time: time | None = Field(default=None, description="Horário fixo (obrigatório para daily/weekly)")
    interval_hours: int | None = Field(default=None, ge=1, le=24, description="Intervalo em horas (obrigatório para interval)")
    weekdays: str | None = Field(
        default=None, description="Dias da semana separados por vírgula, ex.: 'mon,wed,fri' (obrigatório para weekly)"
    )
    timezone: str | None = Field(default=None, description="Fuso horário; se omitido, usa o fuso do usuário")

    @model_validator(mode="after")
    def _validar_campos_por_recorrencia(self) -> "ScheduleCreate":
        if self.recurrence_type in ("daily", "weekly") and self.schedule_time is None:
            raise ValueError("schedule_time é obrigatório para recurrence_type 'daily' ou 'weekly'")
        if self.recurrence_type == "weekly" and not self.weekdays:
            raise ValueError("weekdays é obrigatório para recurrence_type 'weekly'")
        if self.recurrence_type == "interval" and self.interval_hours is None:
            raise ValueError("interval_hours é obrigatório para recurrence_type 'interval'")
        return self


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    medication_id: int
    recurrence_type: str
    schedule_time: time | None
    interval_hours: int | None
    weekdays: str | None
    timezone: str
