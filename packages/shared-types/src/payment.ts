/**
 * Payment session types — what /api/v1/payments/charge emits.
 *
 * The session shape is forward-compatible with Phase 2's native-SDK migration:
 * Stripe + PayPhone native SDKs will populate `sdk_payload`; today every
 * provider returns `webview_url` and an empty `sdk_payload`.
 */

export type ProviderName = 'payphone' | 'de_una';

export interface CreateChargePayload {
  order_id: string;
  provider: ProviderName;
  return_url: string;
}

export interface ChargeSessionResponse {
  session_id: string;
  provider: ProviderName;
  webview_url: string;
  sdk_payload: Record<string, unknown>;
  amount: string;
  currency: string;
  transaction_id: number;
}
