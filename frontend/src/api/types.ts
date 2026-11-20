// Tipos espelhando api/schemas/*.py do backend (fonte única: docs/openapi.yaml).

export type ProfessionalRole = "admin" | "medico" | "enfermeiro" | "outro_profissional";

export interface Professional {
  id: number;
  full_name: string;
  email: string;
  role: ProfessionalRole;
  profession: string;
  council_type: string | null;
  council_number: string | null;
  council_state: string | null;
  institution: string | null;
  verification_status: "pending" | "verified" | "rejected";
  active: boolean;
  mfa_enabled: boolean;
  created_at: string;
}

export interface LoginChallenge {
  pre_auth_token: string;
  purpose: "mfa_setup" | "mfa_verify";
}

export interface MfaSetupStart {
  provisioning_uri: string;
  pre_auth_token: string;
}

export type ScheduleRecurrence = "daily" | "weekly" | "interval";

export interface ScheduleInput {
  recurrence_type: ScheduleRecurrence;
  schedule_time?: string | null;
  interval_hours?: number | null;
  weekdays?: string | null;
  timezone?: string | null;
}

export interface ScheduleOut extends ScheduleInput {
  id: number;
  treatment_medication_id: number;
  timezone: string;
}

export interface Patient {
  id: number;
  full_name: string;
  internal_identifier: string;
  birth_date: string | null;
  contact: string | null;
  telegram_link_status: "not_linked" | "invited" | "linked";
  created_by_professional_id: number;
  created_at: string;
}

export interface PatientInvite {
  invite_id: number;
  token: string;
  telegram_deep_link: string | null;
  instructions: string;
  expires_at: string;
}

export type TreatmentStatus = "draft" | "pending_validation" | "active" | "suspended" | "closed";

export interface TreatmentMedication {
  id: number;
  treatment_plan_id: number;
  medication_name: string;
  active_ingredient: string | null;
  presentation: string | null;
  route: string | null;
  dosage: string;
  dosage_unit: string | null;
  quantity_per_administration: string;
  frequency_description: string | null;
  instructions: string | null;
  start_date: string;
  end_date: string | null;
  status: TreatmentStatus;
  photo_path: string | null;
  linked_medication_id: number | null;
  previous_version_id: number | null;
  created_at: string;
  updated_at: string;
  schedules: ScheduleOut[];
}

export interface ReminderEvent {
  id: number;
  medication_id: number;
  scheduled_datetime: string;
  delivery_datetime: string | null;
  confirmed_datetime: string | null;
  status: "pending" | "delivered" | "confirmed" | "not_taken" | "snoozed" | "expired";
  snooze_count: number;
}

export interface Dashboard {
  total_patients: number;
  active_treatments: number;
  treatments_ending_soon: number;
  reminders_sent: number;
  doses_confirmed: number;
  doses_not_taken: number;
  doses_unconfirmed: number;
}

export interface AuditLog {
  id: number;
  actor_id: number | null;
  actor_role: string;
  action: string;
  resource_type: string;
  resource_id: number | null;
  timestamp: string;
  correlation_id: string;
}

export interface ApiErrorBody {
  detail: string | Array<{ msg: string; loc: (string | number)[] }>;
}
