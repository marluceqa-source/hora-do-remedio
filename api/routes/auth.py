from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.auth import TokenRequest, TokenResponse
from core.security import create_access_token
from services.medication_service import get_or_create_user

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Emite um token de acesso para o usuário do Telegram",
    description=(
        "Autenticação da API é independente do token do bot Telegram (seção 8 do prompt master). "
        "O bot troca o telegram_user_id por um token JWT escopado ao usuário para chamar a API em seu nome."
    ),
)
def issue_token(payload: TokenRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = get_or_create_user(db, payload.telegram_user_id, payload.timezone)
    token, expires_in = create_access_token(user.id)
    return TokenResponse(access_token=token, expires_in=expires_in)
