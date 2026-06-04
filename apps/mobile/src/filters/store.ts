/**
 * Filter state for the browse screen.
 *
 * Lives in Zustand (not URL/router params) because:
 *   - Mobile users don't share/bookmark URLs.
 *   - The browse screen toggles list↔map without unmounting; URL-driven state
 *     would force the screen to bounce between modes.
 *
 * `activeCount` powers the badge on the filter button. `toApiParams` is the
 * single boundary that maps UI state to query-string keys.
 */
import { create } from 'zustand';

import type { BagListParams, BagSort, PickupWindow } from '@layapa/shared-types';

export type DistanceOption = 1 | 3 | 5 | 10;
export type RatingOption = 0 | 4 | 4.5;

export interface FilterState {
  dietary: string[];
  excludeAllergens: string[];
  minPrice: number | null;
  maxPrice: number | null;
  pickupWindow: PickupWindow | null;
  distanceKm: DistanceOption;
  minRating: RatingOption;
  sort: BagSort;
  q: string;

  toggleDietary: (name: string) => void;
  toggleAllergen: (name: string) => void;
  setPrice: (range: { min: number | null; max: number | null }) => void;
  setPickupWindow: (w: PickupWindow | null) => void;
  setDistance: (km: DistanceOption) => void;
  setMinRating: (r: RatingOption) => void;
  setSort: (s: BagSort) => void;
  setSearchQuery: (q: string) => void;
  reset: () => void;

  activeCount: () => number;
  toApiParams: () => BagListParams;
}

const DEFAULTS = {
  dietary: [] as string[],
  excludeAllergens: [] as string[],
  minPrice: null as number | null,
  maxPrice: null as number | null,
  pickupWindow: null as PickupWindow | null,
  distanceKm: 3 as DistanceOption,
  minRating: 0 as RatingOption,
  sort: 'distance' as BagSort,
  q: '',
};

export const useFilterStore = create<FilterState>((set, get) => ({
  ...DEFAULTS,

  toggleDietary: (name) =>
    set((s) => ({
      dietary: s.dietary.includes(name)
        ? s.dietary.filter((n) => n !== name)
        : [...s.dietary, name],
    })),
  toggleAllergen: (name) =>
    set((s) => ({
      excludeAllergens: s.excludeAllergens.includes(name)
        ? s.excludeAllergens.filter((n) => n !== name)
        : [...s.excludeAllergens, name],
    })),
  setPrice: ({ min, max }) => set({ minPrice: min, maxPrice: max }),
  setPickupWindow: (w) => set({ pickupWindow: w }),
  setDistance: (km) => set({ distanceKm: km }),
  setMinRating: (r) => set({ minRating: r }),
  setSort: (s) => set({ sort: s }),
  setSearchQuery: (q) => set({ q }),
  reset: () => set({ ...DEFAULTS }),

  activeCount: () => {
    const s = get();
    let n = 0;
    if (s.dietary.length > 0) n += 1;
    if (s.excludeAllergens.length > 0) n += 1;
    if (s.minPrice !== null || s.maxPrice !== null) n += 1;
    if (s.pickupWindow !== null) n += 1;
    if (s.distanceKm !== DEFAULTS.distanceKm) n += 1;
    if (s.minRating !== DEFAULTS.minRating) n += 1;
    if (s.sort !== DEFAULTS.sort) n += 1;
    return n;
  },

  toApiParams: () => {
    const s = get();
    const params: BagListParams = {
      radius_km: s.distanceKm,
      sort: s.sort,
    };
    if (s.dietary.length > 0) params.dietary = s.dietary;
    if (s.excludeAllergens.length > 0) params.exclude_allergens = s.excludeAllergens;
    if (s.minPrice !== null) params.min_price = s.minPrice;
    if (s.maxPrice !== null) params.max_price = s.maxPrice;
    if (s.pickupWindow !== null) params.pickup_window = s.pickupWindow;
    if (s.minRating > 0) params.min_rating = s.minRating;
    if (s.q.trim()) params.q = s.q.trim();
    return params;
  },
}));
