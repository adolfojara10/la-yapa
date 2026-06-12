/**
 * Business-facing HTTP wrappers. Mirror /api/v1/business/*.
 */
import { apiClient } from './client';

import type {
  BagTemplate,
  BagTemplatePayload,
  BusinessBagDuplicatePayload,
  BusinessBagPayload,
  BusinessDashboardSummary,
  BusinessLocation,
  BusinessLocationPayload,
  BusinessOnboardingPayload,
  BusinessOrder,
  BusinessSummary,
  ConfirmPickupByPinPayload,
  ConfirmPickupByScanPayload,
  DispatchSuspendedPayload,
  ManagedBag,
  SuspendedMealForDispatch,
  UploadAsset,
} from '@layapa/shared-types';

function appendUpload(formData: FormData, key: string, file: UploadAsset | undefined) {
  if (!file) return;
  formData.append(key, {
    uri: file.uri,
    name: file.name,
    type: file.type ?? 'application/octet-stream',
  } as never);
}

function appendValue(formData: FormData, key: string, value: unknown) {
  if (value === undefined || value === null) return;
  if (Array.isArray(value)) {
    formData.append(key, JSON.stringify(value));
    return;
  }
  if (typeof value === 'object') {
    formData.append(key, JSON.stringify(value));
    return;
  }
  formData.append(key, String(value));
}

function buildMultipartFormData(payload: object): FormData {
  const formData = new FormData();
  for (const [key, value] of Object.entries(payload as Record<string, unknown>)) {
    if (value && typeof value === 'object' && 'uri' in (value as Record<string, unknown>)) {
      appendUpload(formData, key, value as UploadAsset);
      continue;
    }
    appendValue(formData, key, value);
  }
  return formData;
}

export async function submitOnboarding(
  payload: BusinessOnboardingPayload,
): Promise<BusinessSummary> {
  const { data } = await apiClient.post<BusinessSummary>(
    '/business/onboarding',
    buildMultipartFormData(payload),
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return data;
}

export async function listLocations(): Promise<BusinessLocation[]> {
  const { data } = await apiClient.get<BusinessLocation[]>('/business/locations');
  return data;
}

export async function createLocation(payload: BusinessLocationPayload): Promise<BusinessLocation> {
  const { data } = await apiClient.post<BusinessLocation>('/business/locations', payload);
  return data;
}

export async function updateLocation(
  id: number,
  payload: Partial<BusinessLocationPayload>,
): Promise<BusinessLocation> {
  const { data } = await apiClient.patch<BusinessLocation>(`/business/locations/${id}`, payload);
  return data;
}

export async function listBags(): Promise<ManagedBag[]> {
  const { data } = await apiClient.get<ManagedBag[]>('/business/bags');
  return data;
}

export async function getManagedBag(id: string): Promise<ManagedBag> {
  const { data } = await apiClient.get<ManagedBag>(`/business/bags/${id}`);
  return data;
}

export async function createBag(payload: BusinessBagPayload): Promise<ManagedBag> {
  const { data } = await apiClient.post<ManagedBag>(
    '/business/bags',
    buildMultipartFormData(payload),
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return data;
}

export async function updateBag(
  id: string,
  payload: Partial<BusinessBagPayload>,
): Promise<ManagedBag> {
  const hasUpload = Object.values(payload).some(
    (value) => value && typeof value === 'object' && 'uri' in (value as object),
  );
  if (hasUpload) {
    const { data } = await apiClient.patch<ManagedBag>(
      `/business/bags/${id}`,
      buildMultipartFormData(payload),
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return data;
  }
  const { data } = await apiClient.patch<ManagedBag>(`/business/bags/${id}`, payload);
  return data;
}

export async function duplicateBag(
  id: string,
  payload: BusinessBagDuplicatePayload = {},
): Promise<ManagedBag> {
  const { data } = await apiClient.post<ManagedBag>(`/business/bags/${id}/duplicate`, payload);
  return data;
}

export async function listBagTemplates(): Promise<BagTemplate[]> {
  const { data } = await apiClient.get<BagTemplate[]>('/business/bag-templates');
  return data;
}

export async function createBagTemplate(payload: BagTemplatePayload): Promise<BagTemplate> {
  const { data } = await apiClient.post<BagTemplate>(
    '/business/bag-templates',
    buildMultipartFormData(payload),
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return data;
}

export async function deleteBagTemplate(id: string): Promise<void> {
  await apiClient.delete(`/business/bag-templates/${id}`);
}

export async function getDashboard(): Promise<BusinessDashboardSummary> {
  const { data } = await apiClient.get<BusinessDashboardSummary>('/business/dashboard');
  return data;
}

export async function listActiveOrders(): Promise<BusinessOrder[]> {
  const { data } = await apiClient.get<BusinessOrder[]>('/business/orders/active');
  return data;
}

export async function listTodayOrders(): Promise<BusinessOrder[]> {
  const { data } = await apiClient.get<BusinessOrder[]>('/business/orders/today');
  return data;
}

export async function getOrder(id: string): Promise<BusinessOrder> {
  const { data } = await apiClient.get<BusinessOrder>(`/business/orders/${id}`);
  return data;
}

export async function confirmPickupByScan(
  payload: ConfirmPickupByScanPayload,
): Promise<BusinessOrder> {
  const { data } = await apiClient.post<BusinessOrder>(
    '/business/orders/confirm-pickup-by-scan',
    payload,
  );
  return data;
}

export async function confirmPickupByPin(
  payload: ConfirmPickupByPinPayload,
): Promise<BusinessOrder> {
  const { data } = await apiClient.post<BusinessOrder>(
    '/business/orders/confirm-pickup-by-pin',
    payload,
  );
  return data;
}

export async function listActiveSuspended(): Promise<SuspendedMealForDispatch[]> {
  const { data } = await apiClient.get<SuspendedMealForDispatch[]>(
    '/business/suspended-meals/active',
  );
  return data;
}

export async function dispatchSuspended(payload: DispatchSuspendedPayload): Promise<{
  claim_id: number;
  donation_id: string;
  business_location_id: number;
  claimed_at: string;
}> {
  const { data } = await apiClient.post('/business/suspended-meals/dispatch', payload);
  return data as never;
}
