import { apiClient } from "./client";
import type { Dashboard } from "./types";

export interface DashboardFilters {
  patient_id?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
}

export async function getDashboard(filters: DashboardFilters = {}): Promise<Dashboard> {
  const { data } = await apiClient.get<Dashboard>("/api/v1/dashboard", { params: filters });
  return data;
}
