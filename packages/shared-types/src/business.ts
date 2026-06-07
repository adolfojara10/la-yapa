/**
 * Business types.
 *
 * Two unrelated concerns share this file:
 *   - `Business` / `BusinessType` / `BusinessStatus`: the domain model
 *     (used by the consumer + admin apps to describe a vendor)
 *   - `BusinessOrder` / `BusinessDashboardSummary` / etc.: payload shapes
 *     emitted by /api/v1/business/* endpoints (used by the business app
 *     when a vendor is logged in)
 *
 * Keeping them in one file because the second set is unambiguously
 * "business-facing API"; another split would be confusing.
 */

import type { OrderStatus, PaymentMethod } from './order';

// ---- domain model (consumer + admin apps) ---------------------------------

export type BusinessType = 'restaurant' | 'bakery' | 'supermarket' | 'hotel' | 'mercado' | 'farmer';

export type BusinessStatus = 'pending' | 'approved' | 'suspended' | 'rejected';

export interface Business {
  id: number;
  name: string;
  type: BusinessType;
  status: BusinessStatus;
  ruc?: string;
  description?: string;
  addressLine: string;
  city: string;
  province: string;
  latitude: number;
  longitude: number;
  logoUrl?: string;
  createdAt: string;
  updatedAt: string;
}

// ---- business-facing API payloads (business app) --------------------------

export interface BusinessOrderBag {
  id: string;
  title: string;
  image_url: string;
  type: 'surprise' | 'specific';
  pickup_window_start: string;
  pickup_window_end: string;
  dietary_tags: string[];
  allergen_warnings: string[];
}

export interface BusinessOrder {
  id: string;
  status: OrderStatus;
  quantity: number;
  sale_price_snapshot: string;
  total_paid: string;
  pickup_code: string;
  payment_method: PaymentMethod | '';
  donate_as_suspended_meal: boolean;
  picked_up_at: string | null;
  created_at: string;
  consumer_first_name: string;
  business_location_id: number;
  business_location_name: string;
  bag: BusinessOrderBag;
  is_within_pickup_window: boolean;
  is_pin_locked: boolean;
}

export interface BusinessDashboardSummary {
  active_orders_count: number;
  today_completed_count: number;
  suspended_meals_available: number;
}

export interface ConfirmPickupByScanPayload {
  qr_token: string;
}

export interface ConfirmPickupByPinPayload {
  business_location_id: number;
  pin: string;
}

export interface ConfirmPickupByIdPayload {
  qr_token?: string;
  pin?: string;
}

export interface SuspendedMealForDispatch {
  id: string;
  amount: string;
  is_anonymous: boolean;
  created_at: string;
  bag_title: string;
  business_location_id: number | null;
  business_location_name: string;
}

export interface DispatchSuspendedPayload {
  donation_id: string;
  business_location_id?: number;
  notes?: string;
}
