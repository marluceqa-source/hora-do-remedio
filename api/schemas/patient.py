from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientCreateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    internal_identifier: str = Field(min_length=1, max_length=100, description="Identificador interno único (não usar CPF)")
    birth_date: date | None = None
    contact: str | None = Field(default=None, max_length=100, description="Só preencher quando autorizado (RF03)")


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    internal_identifier: str
    birth_date: date | None
    contact: str | None
    telegram_link_status: str
    created_by_professional_id: int
    created_at: datetime


class PatientInviteOut(BaseModel):
    invite_id: int
    token: str = Field(description="Só aparece nesta resposta — guarde/entregue ao paciente agora")
    telegram_deep_link: str | None = Field(
        default=None, description="Link clicável (abre o bot direto); None se TELEGRAM_BOT_USERNAME não configurado"
    )
    instructions: str
    expires_at: datetime
