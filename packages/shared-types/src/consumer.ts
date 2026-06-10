/** Filter + query types for /api/v1/consumer/* endpoints. */

export type PickupWindow = 'today' | 'tomorrow' | 'this_week';

export type BagSort = 'distance' | 'price' | 'rating' | 'ending_soon';

export interface BagListParams {
  lat?: number;
  lng?: number;
  radius_km?: number;
  dietary?: string[]; // serialized as CSV
  exclude_allergens?: string[]; // serialized as CSV
  min_price?: number;
  max_price?: number;
  pickup_window?: PickupWindow;
  min_rating?: number;
  q?: string;
  sort?: BagSort;
  cursor?: string;
  page_size?: number;
  is_favorited?: boolean;
}

export interface CursorPage<T> {
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface FavoriteToggleResponse {
  favorited: boolean;
  business_location_id: number;
}
