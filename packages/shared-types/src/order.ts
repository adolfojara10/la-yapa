/**
 * Order types — mirror what /api/v1/consumer/orders emits.
 *
 * Snake_case to match DRF directly (no client-side renaming).
 */

export type OrderStatus =
  | 'pending_payment'
  | 'paid'
  | 'ready_for_pickup'
  | 'completed'
  | 'pending_refund'
  | 'cancelled'
  | 'refunded'
  | 'expired';

export type PaymentMethod = 'payphone' | 'de_una' | 'kushki' | 'stripe' | 'cash';

export type CancelledBy = 'consumer' | 'business' | 'admin' | 'system';

export type BonusCreditSource = 'business_cancellation' | 'referral' | 'promo';

export interface OrderBagSnapshot {
  id: string;
  title: string;
  image_url: string;
  type: 'surprise' | 'specific';
  pickup_window_start: string;
  pickup_window_end: string;
}

export interface OrderBusinessLocation {
  id: number;
  business_name: string;
  name: string;
  address: string;
  phone: string;
  latitude: number | null;
  longitude: number | null;
}

export interface Order {
  id: string;
  status: OrderStatus;
  quantity: number;
  original_price_snapshot: string;
  sale_price_snapshot: string;
  applied_credit_amount: string;
  total_paid: string;
  pickup_code: string;
  pickup_qr_token: string;
  payment_method: PaymentMethod | '';
  donate_as_suspended_meal: boolean;
  cancelled_by: CancelledBy | '';
  cancelled_at: string | null;
  cancellation_reason: string;
  picked_up_at: string | null;
  created_at: string;
  updated_at: string;
  bag: OrderBagSnapshot;
  business_location: OrderBusinessLocation;
  is_within_consumer_cancel_window: boolean;
}

export interface BonusCredit {
  id: number;
  amount: string;
  source: BonusCreditSource;
  expires_at: string | null;
  redeemed_at: string | null;
  notes: string;
  is_available: boolean;
  is_expired: boolean;
}

export interface CreateOrderPayload {
  bag_id: string;
  quantity?: number;
  donate_as_suspended_meal?: boolean;
}

export interface CancelOrderPayload {
  reason?: string;
}

export interface CancelOrderResponse {
  order: Order;
  triggered_refund: boolean;
}

export interface RedeemCreditPayload {
  credit_id: number;
}

export interface RedeemCreditResponse {
  order: Order;
  applied_credit_amount: string;
}
