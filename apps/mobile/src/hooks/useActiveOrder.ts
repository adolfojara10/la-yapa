/**
 * Returns the consumer's most recent order in an actionable state, or null.
 *
 * Powers the "Active order" banner on the Explorar tab. We only show one at
 * a time even if there are several active — the most recent is the most
 * relevant.
 */
import { useMemo } from 'react';

import { useOrders } from './useOrders';

import type { Order, OrderStatus } from '@layapa/shared-types';

const ACTIVE: ReadonlySet<OrderStatus> = new Set([
  'pending_payment',
  'paid',
  'ready_for_pickup',
  'pending_refund',
]);

export function useActiveOrder(): { order: Order | null; isLoading: boolean } {
  const query = useOrders();
  const order = useMemo(() => {
    const results = query.data?.results ?? [];
    return results.find((o) => ACTIVE.has(o.status)) ?? null;
  }, [query.data]);
  return { order, isLoading: query.isLoading };
}
