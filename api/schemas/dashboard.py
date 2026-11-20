from pydantic import BaseModel, Field


class DashboardOut(BaseModel):
    total_patients: int
    active_treatments: int
    treatments_ending_soon: int = Field(description="Tratamentos ativos com término nos próximos 7 dias")
    reminders_sent: int
    doses_confirmed: int
    doses_not_taken: int = Field(description="Declarado explicitamente pelo paciente, não inferido")
    doses_unconfirmed: int = Field(description="Sem resposta — RN12: não significa que o medicamento não foi tomado")
