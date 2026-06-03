/**
 * Auth endpoint wrappers. Pure HTTP — no state.
 *
 * Response shapes mirror packages/shared-types/src/auth.ts. We keep the
 * imports loose (`any` cast for the unused `User` import path) to avoid
 * a brittle dep on the shared-types package layout while we're iterating.
 */
import { apiClient } from './client';

import type {
  AppleLoginPayload,
  AuthResponse,
  AuthTokens,
  ForgotPasswordPayload,
  GoogleLoginPayload,
  LoginPayload,
  LogoutPayload,
  RegisterPayload,
  ResendVerificationPayload,
  ResetPasswordPayload,
  VerifyEmailPayload,
} from '@layapa/shared-types';

export async function register(payload: RegisterPayload): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>('/auth/register', payload);
  return data;
}

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>('/auth/login', payload);
  return data;
}

export async function loginWithGoogle(payload: GoogleLoginPayload): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>('/auth/google', payload);
  return data;
}

export async function loginWithApple(payload: AppleLoginPayload): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>('/auth/apple', payload);
  return data;
}

export async function refresh(refreshToken: string): Promise<AuthTokens> {
  const { data } = await apiClient.post<AuthTokens>('/auth/refresh', { refresh: refreshToken });
  return data;
}

export async function verifyEmail(payload: VerifyEmailPayload): Promise<void> {
  await apiClient.post('/auth/verify-email', payload);
}

export async function resendVerification(payload: ResendVerificationPayload): Promise<void> {
  await apiClient.post('/auth/verify-email/resend', payload);
}

export async function forgotPassword(payload: ForgotPasswordPayload): Promise<void> {
  await apiClient.post('/auth/forgot-password', payload);
}

export async function resetPassword(payload: ResetPasswordPayload): Promise<void> {
  await apiClient.post('/auth/reset-password', payload);
}

export async function logout(payload: LogoutPayload): Promise<void> {
  await apiClient.post('/auth/logout', payload);
}
