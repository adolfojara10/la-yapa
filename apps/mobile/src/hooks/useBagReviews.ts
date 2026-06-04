import { useQuery } from '@tanstack/react-query';

import { bagsApi } from '@/api';

import type { BagReview, CursorPage } from '@layapa/shared-types';

export function useBagReviews(id: string | undefined) {
  return useQuery<CursorPage<BagReview>, Error>({
    queryKey: ['bags', 'reviews', id],
    queryFn: () => bagsApi.getBagReviews(id as string),
    enabled: Boolean(id),
    staleTime: 60_000,
  });
}
