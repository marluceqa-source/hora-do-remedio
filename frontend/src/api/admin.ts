import { apiClient } from "./client";
import type { AuditLog, Professional } from "./types";

export async function listProfessionals(verificationStatus?: string): Promise<Professional[]> {
  const { data } = await apiClient.get<Professional[]>("/api/v1/professionals", {
    params: verificationStatus ? { verification_status: verificationStatus } : undefined,
  });
  return data;
}

export async function verifyProfessional(
  professionalId: number,
  verificationStatus: "verified" | "rejected" | "pending",
): Promise<Professional> {
  const { data } = await apiClient.post<Professional>(`/api/v1/professionals/${professionalId}/verify`, {
    verification_status: verificationStatus,
  });
  return data;
}

export async function listAuditLogs(params: { resource_type?: string; action?: string; limit?: number } = {}): Promise<
  AuditLog[]
> {
  const { data } = await apiClient.get<AuditLog[]>("/api/v1/audit-logs", { params });
  return data;
}
