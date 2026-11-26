from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

# Ambientes em que segredo de exemplo é tolerável. Qualquer outro valor de APP_ENV
# (production, staging, homologacao...) exige segredo real.
DEV_ENVIRONMENTS = frozenset({"development", "dev", "local", "test", "testing"})

MIN_SECRET_LENGTH = 32

GENERATE_SECRET_HINT = 'python -c "import secrets; print(secrets.token_urlsafe(48))"'


def is_weak_secret(value: str) -> bool:
    """Segredo de exemplo, vazio, ou curto demais para assinar um HMAC.

    Pega tanto os padrões deste arquivo quanto os placeholders do .env.example — copiar
    o exemplo e esquecer de editar é justamente o descuido que esta checagem existe para
    interromper.
    """
    normalized = value.strip().lower()
    if len(normalized) < MIN_SECRET_LENGTH:
        return True
    return "change-me" in normalized or "troque" in normalized


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Hora do Remédio"
    app_env: str = "development"
    timezone: str = "America/Sao_Paulo"
    locale: str = "pt-BR"

    telegram_bot_token: str = ""

    database_url: str = "sqlite:///./database/hora_do_remedio.db"

    api_secret_key: str = "change-me"
    api_algorithm: str = "HS256"
    api_access_token_expire_minutes: int = 60

    rate_limit_per_minute: int = 60

    # Depois desta janela sem resposta, o lembrete passa a `expired` (RN12/RN29: "expirado"
    # é "não sabemos", nunca "não tomou"). 24 h deixa a pessoa responder o dia inteiro e só
    # descarta o botão quando o lembrete seguinte do mesmo horário já chegou.
    reminder_expire_hours: int = 24

    data_retention_days: int = 365

    ocr_engine: str = "tesseract"
    ocr_language: str = "por"
    tesseract_cmd: str = ""

    stt_engine: str = "faster-whisper"
    stt_model_size: str = "small"
    stt_language: str = "pt"

    tts_engine: str = "pyttsx3"
    tts_voice_name: str = ""

    log_level: str = "INFO"
    log_file: str = "./logs/hora_do_remedio.log"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- Portal web de profissionais de saúde ---
    professional_session_secret_key: str = "change-me-professional-session"
    professional_session_cookie_name: str = "hdr_professional_session"
    professional_session_expire_minutes: int = 480
    professional_mfa_pre_auth_expire_minutes: int = 5
    professional_max_failed_logins: int = 5
    professional_lockout_minutes: int = 15
    professional_password_reset_expire_minutes: int = 30

    # --- Vínculo paciente ↔ Telegram (RF04) ---
    patient_invite_expire_minutes: int = 30
    # Usado só para montar o link clicável https://t.me/<username>?start=<token> no portal;
    # sem isso, a resposta da API ainda traz o token puro com instruções manuais.
    telegram_bot_username: str = ""

    # --- Portal web — CORS (o frontend roda em outra porta/origem) ---
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _reject_weak_secrets(self) -> "Settings":
        if self.app_env.strip().lower() in DEV_ENVIRONMENTS:
            return self

        weak = [
            name
            for name, value in (
                ("API_SECRET_KEY", self.api_secret_key),
                ("PROFESSIONAL_SESSION_SECRET_KEY", self.professional_session_secret_key),
            )
            if is_weak_secret(value)
        ]
        if weak:
            raise ValueError(
                f"APP_ENV={self.app_env!r} exige segredos reais, mas {', '.join(weak)} "
                f"ainda está com valor de exemplo, vazio, ou com menos de "
                f"{MIN_SECRET_LENGTH} caracteres. Gere cada segredo com "
                f"{GENERATE_SECRET_HINT} e defina no .env."
            )

        if self.api_secret_key == self.professional_session_secret_key:
            raise ValueError(
                "API_SECRET_KEY e PROFESSIONAL_SESSION_SECRET_KEY não podem ter o mesmo "
                "valor: a autenticação do paciente e a do profissional são independentes "
                "de propósito (RN19), e reaproveitar o segredo anula essa separação."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
