import { apiClient } from './client';

import type { FavoriteToggleResponse } from '@layapa/shared-types';

/**
 * Toggle the consumer's favorite on a business location. Idempotent —
 * the server returns the *resulting* state, not whether the row was
 * created or deleted.
 */
export async function toggleFavorite(businessLocationId: number): Promise<FavoriteToggleResponse> {
  const { data } = await apiClient.post<FavoriteToggleResponse>(
    `/consumer/business-locations/${businessLocationId}/favorite`,
  );
  return data;
}
