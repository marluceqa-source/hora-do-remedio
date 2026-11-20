import { apiClient } from "./client";
import type { LoginChallenge, MfaSetupStart, Professional, ProfessionalRole } from "./types";

export interface SignupPayload {
  full_name: string;
  email: string;
  password: string;
  role: ProfessionalRole;
  profession: string;
  council_type?: string;
  council_number?: string;
  council_state?: string;
  institution?: string;
}

export async function signup(payload: SignupPayload): Promise<Professional> {
  const { data } = await apiClient.post<Professional>("/api/v1/professionals", payload);
  return data;
}

export async function loginStep1(email: string, password: string): Promise<LoginChallenge> {
  const { data } = await apiClient.post<LoginChallenge>("/api/v1/auth/professional/login", { email, password });
  return data;
}

export async function startMfaSetup(preAuthToken: string): Promise<MfaSetupStart> {
  const { data } = await apiClient.post<MfaSetupStart>("/api/v1/auth/professional/mfa/setup", {
    pre_auth_token: preAuthToken,
  });
  return data;
}

export async function confirmMfaSetup(preAuthToken: string, code: string): Promise<Professional> {
  const { data } = await apiClient.post<Professional>("/api/v1/auth/professional/mfa/confirm", {
    pre_auth_token: preAuthToken,
    code,
  });
  return data;
}

export async function verifyMfa(preAuthToken: string, code: string): Promise<Professional> {
  const { data } = await apiClient.post<Professional>("/api/v1/auth/professional/mfa/verify", {
    pre_auth_token: preAuthToken,
    code,
  });
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post("/api/v1/auth/professional/logout");
}

export async function getMyProfile(): Promise<Professional> {
  const { data } = await apiClient.get<Professional>("/api/v1/professionals/me");
  return data;
}

export async function requestPasswordReset(email: string): Promise<void> {
  await apiClient.post("/api/v1/auth/professional/password-reset/request", { email });
}

export async function confirmPasswordReset(token: string, newPassword: string): Promise<void> {
  await apiClient.post("/api/v1/auth/professional/password-reset/confirm", {
    token,
    new_password: newPassword,
  });
}
