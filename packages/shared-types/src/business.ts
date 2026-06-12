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

export type BusinessTier = 'formal' | 'informal';

export type BusinessStatus = 'pending' | 'approved' | 'suspended' | 'rejected';

export type PayoutFrequency = 'weekly' | 'monthly';

export type PayoutMethod = 'bank_transfer' | 'de_una';

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
  today_orders_count: number;
  today_revenue: string;
  today_bags_sold: number;
}

export interface BusinessSummary {
  id: number;
  name: string;
  business_type: BusinessType;
  tier: BusinessTier;
  status: BusinessStatus;
  rejection_reason: string;
  payout_method: PayoutMethod;
  has_locations: boolean;
}

export interface BusinessLocation {
  id: number;
  name: string;
  address: string;
  lat: number | null;
  lng: number | null;
  phone: string;
  is_active: boolean;
  hours_of_operation: Record<string, string>;
}

export interface ManagedBag {
  id: string;
  business_location_id: number;
  business_location_name: string;
  type: 'surprise' | 'specific';
  title: string;
  description: string;
  image_url: string;
  original_price: string;
  sale_price: string;
  quantity_available: number;
  quantity_total: number;
  quantity_sold: number;
  pickup_window_start: string;
  pickup_window_end: string;
  dietary_tags: string[];
  allergen_warnings: string[];
  is_active: boolean;
  is_suspended_meal_eligible: boolean;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
}

export interface BagTemplate {
  id: string;
  name: string;
  type: 'surprise' | 'specific';
  title: string;
  description: string;
  image_url: string;
  original_price: string;
  sale_price: string;
  dietary_tags: string[];
  allergen_warnings: string[];
  is_suspended_meal_eligible: boolean;
  created_at: string;
  updated_at: string;
}

export interface BusinessLocationPayload {
  name: string;
  address: string;
  lat: number;
  lng: number;
  phone?: string;
  is_active?: boolean;
  hours_of_operation?: Record<string, string>;
}

export interface BusinessBagPayload {
  business_location_id: number;
  type: 'surprise' | 'specific';
  title: string;
  description?: string;
  image?: UploadAsset;
  original_price: string;
  sale_price: string;
  quantity_available: number;
  pickup_window_start: string;
  pickup_window_end: string;
  dietary_tags?: string[];
  allergen_warnings?: string[];
  is_suspended_meal_eligible?: boolean;
  is_active?: boolean;
}

export interface BusinessBagDuplicatePayload {
  business_location_id?: number;
  quantity_available?: number;
  pickup_window_start?: string;
  pickup_window_end?: string;
}

export interface BagTemplatePayload {
  name: string;
  type: 'surprise' | 'specific';
  title: string;
  description?: string;
  image?: UploadAsset;
  original_price: string;
  sale_price: string;
  dietary_tags?: string[];
  allergen_warnings?: string[];
  is_suspended_meal_eligible?: boolean;
}

export interface UploadAsset {
  uri: string;
  name: string;
  type?: string | null;
}

export interface BusinessOnboardingPayload {
  name: string;
  business_type: BusinessType;
  tier: BusinessTier;
  description?: string;
  phone?: string;
  email?: string;
  website?: string;
  location_name: string;
  address: string;
  lat: number;
  lng: number;
  location_phone?: string;
  hours_of_operation?: Record<string, string>;
  payout_frequency?: PayoutFrequency;
  payout_method: PayoutMethod;
  account_holder: string;
  bank_name?: string;
  account_number?: string;
  account_type?: string;
  deuna_phone?: string;
  cedula_number: string;
  ruc_number?: string;
  has_food_handling?: boolean;
  food_safety_terms_accepted: boolean;
  ruc_document?: UploadAsset;
  cedula_document?: UploadAsset;
  selfie_with_cedula?: UploadAsset;
  permiso_funcionamiento?: UploadAsset;
  arcsa_document?: UploadAsset;
  bank_proof?: UploadAsset;
  business_photo?: UploadAsset;
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
