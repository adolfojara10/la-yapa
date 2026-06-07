import { useQuery } from '@tanstack/react-query';

import { businessApi } from '@/api';

import type { BusinessOrder } from '@layapa/shared-types';

/** Active orders across all owned locations, sorted by pickup window. */
export function useBusinessActiveOrders() {
  return useQuery<BusinessOrder[], Error>({
    queryKey: ['business', 'orders', 'active'],
    queryFn: () => businessApi.listActiveOrders(),
    // Aggressive freshness for the live worklist — vendors expect updates
    // within seconds of a new payment landing.
    refetchInterval: 15_000,
    staleTime: 0,
  });
}

export function useBusinessOrder(id: string | undefined) {
  return useQuery<BusinessOrder, Error>({
    queryKey: ['business', 'orders', 'detail', id],
    queryFn: () => businessApi.getOrder(id as string),
    enabled: Boolean(id),
    staleTime: 0,
  });
}
