from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.config import get_settings
from database.connection import get_db
from database.models import User

settings = get_settings()
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Token JWT emitido por POST /api/v1/auth/token (independente do token do bot Telegram).",
)

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciais ausentes, inválidas ou expiradas",
)


def create_access_token(user_id: int) -> tuple[str, int]:
    expire_minutes = settings.api_access_token_expire_minutes
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"sub": str(user_id), "exp": expire_at}
    token = jwt.encode(payload, settings.api_secret_key, algorithm=settings.api_algorithm)
    return token, expire_minutes * 60


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.api_secret_key, algorithms=[settings.api_algorithm])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise _CREDENTIALS_ERROR from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _CREDENTIALS_ERROR
    user_id = decode_access_token(credentials.credentials)
    user = db.get(User, user_id)
    if user is None:
        raise _CREDENTIALS_ERROR
    return user
