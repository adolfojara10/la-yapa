/**
 * Business-facing HTTP wrappers. Mirror /api/v1/business/*.
 */
import { apiClient } from './client';

import type {
  BusinessDashboardSummary,
  BusinessOrder,
  ConfirmPickupByPinPayload,
  ConfirmPickupByScanPayload,
  DispatchSuspendedPayload,
  SuspendedMealForDispatch,
} from '@layapa/shared-types';

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
