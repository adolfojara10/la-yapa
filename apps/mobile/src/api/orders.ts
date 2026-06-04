/**
 * Order HTTP wrappers. Mirror /api/v1/consumer/orders.
 */
import { apiClient } from './client';

import type {
  BonusCredit,
  CancelOrderPayload,
  CancelOrderResponse,
  CreateOrderPayload,
  CursorPage,
  Order,
  RedeemCreditPayload,
  RedeemCreditResponse,
} from '@layapa/shared-types';

export async function createOrder(payload: CreateOrderPayload): Promise<Order> {
  const { data } = await apiClient.post<Order>('/consumer/orders', payload);
  return data;
}

export async function listOrders(): Promise<CursorPage<Order>> {
  const { data } = await apiClient.get<CursorPage<Order>>('/consumer/orders');
  return data;
}

export async function getOrder(id: string): Promise<Order> {
  const { data } = await apiClient.get<Order>(`/consumer/orders/${id}`);
  return data;
}

export async function cancelOrder(
  id: string,
  payload: CancelOrderPayload = {},
): Promise<CancelOrderResponse> {
  const { data } = await apiClient.post<CancelOrderResponse>(
    `/consumer/orders/${id}/cancel`,
    payload,
  );
  return data;
}

export async function redeemCredit(
  id: string,
  payload: RedeemCreditPayload,
): Promise<RedeemCreditResponse> {
  const { data } = await apiClient.post<RedeemCreditResponse>(
    `/consumer/orders/${id}/redeem-credit`,
    payload,
  );
  return data;
}

export async function listBonusCredits(): Promise<BonusCredit[]> {
  const { data } = await apiClient.get<BonusCredit[]>('/consumer/bonus-credits');
  return data;
}
