/**
 * Infinite-scroll wrapper around `/consumer/bags`.
 *
 * Filter state lives in the Zustand store (`@/filters/store`). The hook
 * reads it directly so any component can call `useInfiniteBags()` without
 * threading params, and any filter change automatically invalidates the
 * query (the store's reactive subscription updates the queryKey).
 */
import { useInfiniteQuery } from '@tanstack/react-query';

import { bagsApi } from '@/api';
import { useFilterStore } from '@/filters/store';

import type { BagListItem, BagListParams, CursorPage } from '@layapa/shared-types';

export interface UseInfiniteBagsOptions {
  location: { lat: number; lng: number } | null;
}

export function useInfiniteBags({ location }: UseInfiniteBagsOptions) {
  const dietary = useFilterStore((s) => s.dietary);
  const excludeAllergens = useFilterStore((s) => s.excludeAllergens);
  const minPrice = useFilterStore((s) => s.minPrice);
  const maxPrice = useFilterStore((s) => s.maxPrice);
  const pickupWindow = useFilterStore((s) => s.pickupWindow);
  const distanceKm = useFilterStore((s) => s.distanceKm);
  const minRating = useFilterStore((s) => s.minRating);
  const sort = useFilterStore((s) => s.sort);
  const q = useFilterStore((s) => s.q);

  const filters: BagListParams = {
    radius_km: distanceKm,
    sort,
    ...(dietary.length > 0 ? { dietary } : {}),
    ...(excludeAllergens.length > 0 ? { exclude_allergens: excludeAllergens } : {}),
    ...(minPrice !== null ? { min_price: minPrice } : {}),
    ...(maxPrice !== null ? { max_price: maxPrice } : {}),
    ...(pickupWindow !== null ? { pickup_window: pickupWindow } : {}),
    ...(minRating > 0 ? { min_rating: minRating } : {}),
    ...(q.trim() ? { q: q.trim() } : {}),
  };

  const params: BagListParams = {
    ...filters,
    ...(location ? { lat: location.lat, lng: location.lng } : {}),
  };

  return useInfiniteQuery<
    CursorPage<BagListItem>,
    Error,
    { pages: CursorPage<BagListItem>[]; pageParams: (string | null)[] },
    readonly unknown[],
    string | null
  >({
    queryKey: ['bags', 'list', params],
    initialPageParam: null,
    queryFn: async ({ pageParam }) =>
      pageParam ? bagsApi.listBagsFromCursor(pageParam) : bagsApi.listBags(params),
    getNextPageParam: (last) => last.next ?? null,
    staleTime: 30_000, // refetches when navigating back from detail.
  });
}
