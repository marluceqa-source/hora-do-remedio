from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    telegram_user_id: int = Field(description="Identificador numérico do usuário no Telegram")
    timezone: str = Field(default="America/Sao_Paulo", description="Fuso horário do usuário")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Tempo de expiração do token em segundos")
