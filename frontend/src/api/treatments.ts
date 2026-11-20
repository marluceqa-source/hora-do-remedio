import { apiClient } from "./client";
import type { ScheduleInput, TreatmentMedication } from "./types";

export interface TreatmentMedicationPayload {
  medication_name: string;
  active_ingredient?: string | null;
  presentation?: string | null;
  route?: string | null;
  dosage: string;
  dosage_unit?: string | null;
  quantity_per_administration: string;
  frequency_description?: string | null;
  instructions?: string | null;
  start_date: string;
  end_date?: string | null;
  photo_path?: string | null;
  schedules: ScheduleInput[];
}

export async function createTreatmentMedication(
  patientId: number,
  payload: TreatmentMedicationPayload,
): Promise<TreatmentMedication> {
  const { data } = await apiClient.post<TreatmentMedication>(`/api/v1/patients/${patientId}/medications`, payload);
  return data;
}

export async function updateTreatmentMedication(
  treatmentMedicationId: number,
  payload: Partial<TreatmentMedicationPayload>,
): Promise<TreatmentMedication> {
  const { data } = await apiClient.patch<TreatmentMedication>(
    `/api/v1/treatment-medications/${treatmentMedicationId}`,
    payload,
  );
  return data;
}

export async function activateTreatmentMedication(treatmentMedicationId: number): Promise<TreatmentMedication> {
  const { data } = await apiClient.post<TreatmentMedication>(
    `/api/v1/treatment-medications/${treatmentMedicationId}/activate`,
  );
  return data;
}

export async function suspendTreatmentMedication(treatmentMedicationId: number): Promise<TreatmentMedication> {
  const { data } = await apiClient.post<TreatmentMedication>(
    `/api/v1/treatment-medications/${treatmentMedicationId}/suspend`,
  );
  return data;
}

export async function getTreatmentMedicationVersions(treatmentMedicationId: number): Promise<TreatmentMedication[]> {
  const { data } = await apiClient.get<TreatmentMedication[]>(
    `/api/v1/treatment-medications/${treatmentMedicationId}/versions`,
  );
  return data;
}
