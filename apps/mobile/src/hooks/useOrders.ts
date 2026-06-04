import { useQuery } from '@tanstack/react-query';

import { ordersApi } from '@/api';

import type { CursorPage, Order } from '@layapa/shared-types';

/** Order history (single page for now — pagination wired but UI uses first page only). */
export function useOrders() {
  return useQuery<CursorPage<Order>, Error>({
    queryKey: ['orders', 'list'],
    queryFn: () => ordersApi.listOrders(),
    staleTime: 30_000,
  });
}
