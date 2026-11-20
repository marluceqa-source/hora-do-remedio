from datetime import date, datetime, time, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("telegram_user_id", name="uq_users_telegram_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Sao_Paulo")
    accessibility_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    medications: Mapped[list["Medication"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    caregiver_accesses: Mapped[list["CaregiverAccess"]] = relationship(
        back_populates="user",
        foreign_keys="CaregiverAccess.user_id",
        cascade="all, delete-orphan",
    )


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[str] = mapped_column(String(100), nullable=False)
    instructions: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # RF02: "Descrição opcional por áudio" — texto que, quando presente, é falado (TTS) no
    # lembrete no lugar do texto padrão. Não é uma dosagem/prescrição nova (RN13): é só a
    # frase que o próprio usuário quer ouvir ao ser lembrado.
    audio_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship(back_populates="medications")
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="medication", cascade="all, delete-orphan")
    reminder_events: Mapped[list["ReminderEvent"]] = relationship(
        back_populates="medication", cascade="all, delete-orphan"
    )


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (
        CheckConstraint(
            "recurrence_type IN ('daily', 'weekly', 'interval')",
            name="ck_schedules_recurrence_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    medication_id: Mapped[int] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recurrence_type: Mapped[str] = mapped_column(String(20), nullable=False)
    schedule_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    interval_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weekdays: Mapped[str | None] = mapped_column(String(20), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Sao_Paulo")

    medication: Mapped["Medication"] = relationship(back_populates="schedules")


class ReminderEvent(Base):
    __tablename__ = "reminder_events"
    __table_args__ = (
        UniqueConstraint("medication_id", "scheduled_datetime", name="uq_reminder_events_medication_schedule"),
        CheckConstraint(
            "status IN ('pending', 'delivered', 'confirmed', 'not_taken', 'snoozed', 'expired')",
            name="ck_reminder_events_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    medication_id: Mapped[int] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Convenção: scheduled_datetime é "naive", representando o horário de parede (wall-clock)
    # no fuso do próprio Schedule/usuário (RN07) — não é um instante UTC. delivery_datetime e
    # confirmed_datetime são instantes reais (quando o evento de fato ocorreu).
    scheduled_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    delivery_datetime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmed_datetime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    snooze_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    medication: Mapped["Medication"] = relationship(back_populates="reminder_events")


class CaregiverAccess(Base):
    __tablename__ = "caregiver_access"
    __table_args__ = (
        UniqueConstraint("user_id", "caregiver_id", name="uq_caregiver_access_user_caregiver"),
        CheckConstraint(
            "permission IN ('view', 'manage')",
            name="ck_caregiver_access_permission",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    caregiver_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission: Mapped[str] = mapped_column(String(20), nullable=False, default="view")
    authorized_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="caregiver_accesses", foreign_keys=[user_id])


# ---------------------------------------------------------------------------
# Portal web para profissionais de saúde (complemento ao bot/API já existentes)
# ---------------------------------------------------------------------------


class Professional(Base):
    __tablename__ = "professionals"
    __table_args__ = (
        UniqueConstraint("email", name="uq_professionals_email"),
        CheckConstraint(
            "role IN ('admin', 'medico', 'enfermeiro', 'outro_profissional')",
            name="ck_professionals_role",
        ),
        CheckConstraint(
            "verification_status IN ('pending', 'verified', 'rejected')",
            name="ck_professionals_verification_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Papel usado pelo RBAC (seção 3). "profession" abaixo é só texto descritivo para exibição.
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="outro_profissional")
    profession: Mapped[str] = mapped_column(String(100), nullable=False)
    council_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    council_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    council_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    institution: Mapped[str | None] = mapped_column(String(200), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # MFA (TOTP): segredo só existe depois que o profissional ativa o 2º fator.
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    patient_links: Mapped[list["PatientProfessionalLink"]] = relationship(back_populates="professional")


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        UniqueConstraint("internal_identifier", name="uq_patients_internal_identifier"),
        UniqueConstraint("user_id", name="uq_patients_user_id"),
        CheckConstraint(
            "telegram_link_status IN ('not_linked', 'invited', 'linked')",
            name="ck_patients_telegram_link_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    internal_identifier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Só preenchido quando o paciente/cuidador autoriza um contato (RF03: "quando autorizado").
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Preenchido somente após o vínculo seguro com o Telegram (RF04) — None até lá.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    telegram_link_status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_linked")
    created_by_professional_id: Mapped[int] = mapped_column(
        ForeignKey("professionals.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    user: Mapped["User | None"] = relationship()
    professional_links: Mapped[list["PatientProfessionalLink"]] = relationship(back_populates="patient")
    treatment_plans: Mapped[list["TreatmentPlan"]] = relationship(back_populates="patient")
    invitations: Mapped[list["PatientInvitation"]] = relationship(back_populates="patient")


class PatientProfessionalLink(Base):
    """RN21/RN22: vínculo autorizado entre paciente e profissional — controla quem vê o quê."""

    __tablename__ = "patient_professional_links"
    __table_args__ = (
        UniqueConstraint("patient_id", "professional_id", name="uq_patient_professional_link"),
        CheckConstraint(
            "authorization_status IN ('pending', 'active', 'revoked')",
            name="ck_patient_professional_link_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    professional_id: Mapped[int] = mapped_column(
        ForeignKey("professionals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, default="responsavel")
    authorization_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    patient: Mapped["Patient"] = relationship(back_populates="professional_links")
    professional: Mapped["Professional"] = relationship(back_populates="patient_links")


class TreatmentPlan(Base):
    """Contêiner do esquema terapêutico autorado pelo profissional (RF05). Só vira lembrete de
    verdade quando RF06/RN26 o ativa, materializando as entidades Medication/Schedule já
    existentes — por isso TreatmentPlan/TreatmentMedication não duplicam o agendador."""

    __tablename__ = "treatment_plans"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'pending_validation', 'active', 'suspended', 'closed')",
            name="ck_treatment_plans_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    professional_id: Mapped[int] = mapped_column(
        ForeignKey("professionals.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    patient: Mapped["Patient"] = relationship(back_populates="treatment_plans")
    medications: Mapped[list["TreatmentMedication"]] = relationship(
        back_populates="treatment_plan", cascade="all, delete-orphan"
    )


class TreatmentMedication(Base):
    __tablename__ = "treatment_medications"
    __table_args__ = (
        UniqueConstraint("linked_medication_id", name="uq_treatment_medications_linked_medication"),
        CheckConstraint(
            "status IN ('draft', 'pending_validation', 'active', 'suspended', 'closed')",
            name="ck_treatment_medications_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    treatment_plan_id: Mapped[int] = mapped_column(
        ForeignKey("treatment_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    medication_name: Mapped[str] = mapped_column(String(200), nullable=False)
    active_ingredient: Mapped[str | None] = mapped_column(String(200), nullable=True)
    presentation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    route: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    dosage_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quantity_per_administration: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency_description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    instructions: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    photo_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # Preenchido só na ativação (RF06) — aponta para o Medication "de verdade" que o
    # scheduler/bot já sabem consumir. RN28: suspender desativa esse Medication (active=False).
    linked_medication_id: Mapped[int | None] = mapped_column(
        ForeignKey("medications.id", ondelete="SET NULL"), nullable=True
    )
    # RN27: editar um tratamento ativo cria uma nova versão em vez de sobrescrever a anterior.
    previous_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("treatment_medications.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    treatment_plan: Mapped["TreatmentPlan"] = relationship(back_populates="medications")
    schedules: Mapped[list["TreatmentMedicationSchedule"]] = relationship(
        back_populates="treatment_medication", cascade="all, delete-orphan"
    )
    linked_medication: Mapped["Medication | None"] = relationship()


class TreatmentMedicationSchedule(Base):
    __tablename__ = "treatment_medication_schedules"
    __table_args__ = (
        CheckConstraint(
            "recurrence_type IN ('daily', 'weekly', 'interval')",
            name="ck_treatment_medication_schedules_recurrence_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    treatment_medication_id: Mapped[int] = mapped_column(
        ForeignKey("treatment_medications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recurrence_type: Mapped[str] = mapped_column(String(20), nullable=False)
    schedule_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    interval_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weekdays: Mapped[str | None] = mapped_column(String(20), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Sao_Paulo")

    treatment_medication: Mapped["TreatmentMedication"] = relationship(back_populates="schedules")


class PatientInvitation(Base):
    """RF04/RN23/RN24: convite único e temporário para vincular o paciente ao bot."""

    __tablename__ = "patient_invitations"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_patient_invitations_token_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_professional_id: Mapped[int] = mapped_column(
        ForeignKey("professionals.id", ondelete="RESTRICT"), nullable=False
    )
    # Nunca armazenar o token em texto puro — só o hash (o paciente recebe o token real 1x).
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    patient: Mapped["Patient"] = relationship(back_populates="invitations")


class AuditLog(Base):
    """RN32: toda operação sensível do portal deve ser auditável."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # None para eventos de sistema (ex.: expurgo automático) sem um ator humano.
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_role: Mapped[str] = mapped_column(String(30), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow, index=True)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False)


class ProfessionalSession(Base):
    """Sessão de portal, revogável no servidor (RF01: expiração, logout, auditoria).

    O cookie guarda um token opaco aleatório; só o hash dele é persistido (mesmo padrão de
    PatientInvitation.token_hash), então um vazamento do banco não expõe sessões utilizáveis.
    """

    __tablename__ = "professional_sessions"
    __table_args__ = (UniqueConstraint("session_token_hash", name="uq_professional_sessions_token_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    professional_id: Mapped[int] = mapped_column(
        ForeignKey("professionals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    professional: Mapped["Professional"] = relationship()


class ProfessionalPasswordResetToken(Base):
    """RF01: "Recuperação de acesso" — token de uso único e com validade curta."""

    __tablename__ = "professional_password_reset_tokens"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_professional_password_reset_token_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    professional_id: Mapped[int] = mapped_column(
        ForeignKey("professionals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    professional: Mapped["Professional"] = relationship()
