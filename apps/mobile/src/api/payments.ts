import { apiClient } from './client';

import type { ChargeSessionResponse, CreateChargePayload } from '@layapa/shared-types';

export async function createCharge(payload: CreateChargePayload): Promise<ChargeSessionResponse> {
  const { data } = await apiClient.post<ChargeSessionResponse>('/payments/charge', payload);
  return data;
}
