'use client';

import type { User } from '@layapa/shared-types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';
const ACCESS_KEY = 'layapa_admin_access';
const REFRESH_KEY = 'layapa_admin_refresh';

export interface AdminBusinessListItem {
  id: number;
  name: string;
  business_type: string;
  tier: string;
  status: string;
  owner_email: string;
  created_at: string;
  has_locations: boolean;
}

export interface AdminBusinessLocation {
  id: number;
  name: string;
  address: string;
  lat: number | null;
  lng: number | null;
  phone: string;
  is_active: boolean;
  hours_of_operation: Record<string, string>;
}

export interface AdminBusinessVerification {
  ruc_number: string;
  ruc_document_url: string;
  cedula_number: string;
  cedula_document_url: string;
  selfie_with_cedula_url: string;
  permiso_funcionamiento_url: string;
  arcsa_url: string;
  bank_proof_url: string;
  business_photo_url: string;
  food_safety_terms_accepted_at: string | null;
}

export interface AdminBusinessDetail extends AdminBusinessListItem {
  description: string;
  phone: string;
  email: string;
  website: string;
  rejection_reason: string;
  review_notes: string;
  owner_phone: string;
  payout_frequency: string;
  payout_method: string;
  approved_at: string | null;
  locations: AdminBusinessLocation[];
  verification: AdminBusinessVerification | null;
}

export interface LoginResponse {
  user: User;
  tokens: { access: string; refresh: string };
}

export interface SalesDraftPayload {
  owner_email: string;
  owner_phone?: string;
  business_name: string;
  business_type: string;
  tier: string;
  description?: string;
  business_phone?: string;
  business_email?: string;
  website?: string;
  payout_frequency?: string;
  payout_method?: string;
  location_name?: string;
  address?: string;
  lat?: number;
  lng?: number;
}

function getTokens() {
  if (typeof window === 'undefined') {
    return { access: null, refresh: null };
  }
  return {
    access: window.localStorage.getItem(ACCESS_KEY),
    refresh: window.localStorage.getItem(REFRESH_KEY),
  };
}

export function persistTokens(tokens: { access: string; refresh: string } | null) {
  if (typeof window === 'undefined') return;
  if (!tokens) {
    window.localStorage.removeItem(ACCESS_KEY);
    window.localStorage.removeItem(REFRESH_KEY);
    return;
  }
  window.localStorage.setItem(ACCESS_KEY, tokens.access);
  window.localStorage.setItem(REFRESH_KEY, tokens.refresh);
}

async function refreshAccessToken(): Promise<string | null> {
  const { refresh } = getTokens();
  if (!refresh) return null;
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) {
    persistTokens(null);
    return null;
  }
  const data = (await response.json()) as { access: string; refresh?: string };
  persistTokens({ access: data.access, refresh: data.refresh ?? refresh });
  return data.access;
}

export async function adminFetch<T>(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<T> {
  const { access } = getTokens();
  const headers = new Headers(init.headers);
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json');
  }
  if (access) {
    headers.set('Authorization', `Bearer ${access}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (response.status === 401 && retry) {
    const nextAccess = await refreshAccessToken();
    if (nextAccess) {
      return adminFetch<T>(path, init, false);
    }
  }
  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(errorBody.detail ?? 'Request failed');
  }
  return (await response.json()) as T;
}

export async function login(payload: { email: string; password: string }): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(errorBody.detail ?? 'Invalid credentials');
  }
  const data = (await response.json()) as LoginResponse;
  persistTokens(data.tokens);
  return data;
}

export async function logout() {
  const { refresh } = getTokens();
  if (refresh) {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    }).catch(() => null);
  }
  persistTokens(null);
}

export async function fetchAdminSession() {
  return adminFetch<User>('/admin/session');
}

export async function fetchBusinesses(status: string) {
  return adminFetch<AdminBusinessListItem[]>(`/admin/businesses?status=${status}`);
}

export async function fetchBusiness(id: number) {
  return adminFetch<AdminBusinessDetail>(`/admin/businesses/${id}`);
}

export async function approveBusiness(id: number) {
  return adminFetch<AdminBusinessDetail>(`/admin/businesses/${id}/approve`, { method: 'POST' });
}

export async function rejectBusiness(id: number, reason: string) {
  return adminFetch<AdminBusinessDetail>(`/admin/businesses/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

export async function requestMoreInfo(id: number, reason: string) {
  return adminFetch<AdminBusinessDetail>(`/admin/businesses/${id}/request-more-info`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

export async function createSalesDraft(payload: SalesDraftPayload) {
  return adminFetch<AdminBusinessDetail>('/admin/sales/business-accounts', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function sendSetupLink(id: number) {
  return adminFetch<{ sent: boolean; business_id: number; owner_email: string }>(
    `/admin/sales/business-accounts/${id}/send-setup-link`,
    { method: 'POST' },
  );
}

export async function resetPassword(payload: { token: string; new_password: string }) {
  const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as {
      new_password?: string;
      token?: string;
    };
    throw new Error(
      errorBody.new_password ?? errorBody.token ?? 'No pudimos actualizar la contraseña.',
    );
  }
  return (await response.json()) as { ok: boolean };
}
