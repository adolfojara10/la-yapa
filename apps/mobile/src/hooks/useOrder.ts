/**
 * Single-order query with polling for non-terminal statuses.
 *
 * Why polling: payment success arrives via webhook (server-side). The mobile
 * client never sees that directly; the only signal is `GET /orders/{id}`
 * flipping status. We poll every 2 seconds while the order is in a
 * transitional state, then stop.
 *
 * Terminal statuses (no further changes expected): completed, cancelled,
 * refunded, expired. Pending_refund is NOT terminal — it can flip to
 * refunded once the provider confirms.
 */
import { useQuery } from '@tanstack/react-query';

import { ordersApi } from '@/api';

import type { Order, OrderStatus } from '@layapa/shared-types';

const POLL_WHILE: ReadonlySet<OrderStatus> = new Set([
  'pending_payment',
  'paid',
  'ready_for_pickup',
  'pending_refund',
]);

export function useOrder(id: string | undefined) {
  return useQuery<Order, Error>({
    queryKey: ['orders', 'detail', id],
    queryFn: () => ordersApi.getOrder(id as string),
    enabled: Boolean(id),
    // Poll while the order is in a non-terminal state.
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2_000;
      return POLL_WHILE.has(data.status) ? 2_000 : false;
    },
    refetchIntervalInBackground: false,
    staleTime: 0,
  });
}
