from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

ProfessionalRole = Literal["admin", "medico", "enfermeiro", "outro_profissional"]


class ProfessionalSignupRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: ProfessionalRole
    profession: str = Field(min_length=1, max_length=100)
    council_type: str | None = Field(default=None, max_length=20)
    council_number: str | None = Field(default=None, max_length=50)
    council_state: str | None = Field(default=None, max_length=2)
    institution: str | None = Field(default=None, max_length=200)


class ProfessionalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    role: str
    profession: str
    council_type: str | None
    council_number: str | None
    council_state: str | None
    institution: str | None
    verification_status: str
    active: bool
    mfa_enabled: bool
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginChallengeOut(BaseModel):
    pre_auth_token: str
    purpose: Literal["mfa_setup", "mfa_verify"] = Field(
        description="mfa_setup: 1º login, precisa configurar o MFA. mfa_verify: já tem MFA, envie o código."
    )


class PreAuthTokenRequest(BaseModel):
    pre_auth_token: str


class MfaSetupStartResponse(BaseModel):
    provisioning_uri: str = Field(description="otpauth:// URI — renderize como QR Code no frontend")
    pre_auth_token: str


class MfaCodeRequest(BaseModel):
    pre_auth_token: str
    code: str = Field(min_length=6, max_length=6)


class ProfessionalVerifyRequest(BaseModel):
    verification_status: Literal["verified", "rejected", "pending"]


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
