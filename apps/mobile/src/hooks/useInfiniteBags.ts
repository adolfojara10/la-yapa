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
  const filters = useFilterStore((s) => s.toApiParams());
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
