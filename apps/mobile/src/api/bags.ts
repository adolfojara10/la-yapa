/**
 * Bag list + detail HTTP wrappers.
 *
 * Pagination shape mirrors DRF's CursorPagination response:
 *   { next: url|null, previous: url|null, results: [...] }
 *
 * Hooks (useInfiniteBags etc.) build on top — these are the raw fetchers.
 */
import { apiClient } from './client';

import type {
  BagDetail,
  BagListItem,
  BagListParams,
  BagReview,
  CursorPage,
} from '@layapa/shared-types';

function toQueryParams(params: BagListParams): Record<string, string | number> {
  const out: Record<string, string | number> = {};
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    if (Array.isArray(v)) {
      if (v.length > 0) out[k] = v.join(',');
    } else {
      out[k] = v as string | number;
    }
  }
  return out;
}

export async function listBags(params: BagListParams = {}): Promise<CursorPage<BagListItem>> {
  const { data } = await apiClient.get<CursorPage<BagListItem>>('/consumer/bags', {
    params: toQueryParams(params),
  });
  return data;
}

/**
 * Page-2+ fetcher used by TanStack `useInfiniteQuery`. The cursor URL is
 * absolute (DRF embeds the full host), so we strip the base and hand the
 * tail to apiClient — keeps it on the same axios instance and inherits the
 * Bearer token + 401 refresh.
 */
export async function listBagsFromCursor(absoluteUrl: string): Promise<CursorPage<BagListItem>> {
  const baseURL = apiClient.defaults.baseURL ?? '';
  const tail = absoluteUrl.startsWith(baseURL) ? absoluteUrl.slice(baseURL.length) : absoluteUrl;
  const { data } = await apiClient.get<CursorPage<BagListItem>>(tail);
  return data;
}

export async function getBag(
  id: string,
  params: { lat?: number; lng?: number } = {},
): Promise<BagDetail> {
  const { data } = await apiClient.get<BagDetail>(`/consumer/bags/${id}`, {
    params,
  });
  return data;
}

export async function getBagReviews(id: string): Promise<CursorPage<BagReview>> {
  const { data } = await apiClient.get<CursorPage<BagReview>>(`/consumer/bags/${id}/reviews`);
  return data;
}

// Exposed for unit tests.
export const _internal = { toQueryParams };
