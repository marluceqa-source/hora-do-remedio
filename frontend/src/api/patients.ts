import { apiClient } from "./client";
import type { Patient, PatientInvite, ReminderEvent, TreatmentMedication } from "./types";

export interface PatientCreatePayload {
  full_name: string;
  internal_identifier: string;
  birth_date?: string | null;
  contact?: string | null;
}

export async function listPatients(): Promise<Patient[]> {
  const { data } = await apiClient.get<Patient[]>("/api/v1/patients");
  return data;
}

export async function createPatient(payload: PatientCreatePayload): Promise<Patient> {
  const { data } = await apiClient.post<Patient>("/api/v1/patients", payload);
  return data;
}

export async function getPatient(patientId: number): Promise<Patient> {
  const { data } = await apiClient.get<Patient>(`/api/v1/patients/${patientId}`);
  return data;
}

export async function createPatientInvite(patientId: number): Promise<PatientInvite> {
  const { data } = await apiClient.post<PatientInvite>(`/api/v1/patients/${patientId}/invites`);
  return data;
}

export async function listPatientMedications(patientId: number): Promise<TreatmentMedication[]> {
  const { data } = await apiClient.get<TreatmentMedication[]>(`/api/v1/patients/${patientId}/medications`);
  return data;
}

export async function getPatientHistory(
  patientId: number,
  period: "day" | "week" | "month" = "week",
): Promise<ReminderEvent[]> {
  const { data } = await apiClient.get<ReminderEvent[]>(`/api/v1/patients/${patientId}/history`, {
    params: { period },
  });
  return data;
}
