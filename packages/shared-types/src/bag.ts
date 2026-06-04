/**
 * Bag types — mirror what /api/v1/consumer/bags emits.
 *
 * Snake_case keys to match DRF directly (no client-side renaming layer).
 */

export type BagType = 'surprise' | 'specific';

export interface BusinessForCard {
  id: number;
  location_id: number;
  name: string;
  logo_url?: string;
  address: string;
  latitude: number | null;
  longitude: number | null;
  rating_average: number | null;
  rating_count: number;
}

/** Lean payload returned by /consumer/bags (list). */
export interface BagListItem {
  id: string; // UUID
  title: string;
  type: BagType;
  image_url: string;
  original_price: string; // DRF DecimalField serializes as string
  sale_price: string;
  discount_percent: number;
  quantity_available: number;
  pickup_window_start: string;
  pickup_window_end: string;
  business: BusinessForCard;
  distance_m: number | null;
  is_favorited: boolean;
  dietary_tags: string[];
  allergen_warnings: string[];
}

export interface BagReview {
  id: number;
  rating: number;
  comment: string;
  consumer_first_name: string;
  consumer_avatar_url: string;
  created_at: string;
}

/** Full payload returned by /consumer/bags/{id} (detail). */
export interface BagDetail extends BagListItem {
  description: string;
  extra_image_urls: string[];
  business_hours: Record<string, string>;
  business_phone: string;
  latest_reviews: BagReview[];
  is_active: boolean;
  quantity_total: number;
}
