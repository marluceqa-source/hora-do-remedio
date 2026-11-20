from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


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


@lru_cache
def get_settings() -> Settings:
    return Settings()
