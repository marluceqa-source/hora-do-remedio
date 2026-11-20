from pydantic import BaseModel, Field


class ReportOut(BaseModel):
    total_scheduled: int
    total_confirmed: int
    total_not_taken: int = Field(description="Doses marcadas como não tomadas, conforme declaração do usuário")
    total_unconfirmed: int = Field(description="Doses sem confirmação (ausência de resposta, RN12)")
    confirmation_rate: float = Field(description="Percentual de confirmação declarada, de 0 a 100")
