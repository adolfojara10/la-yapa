import { useQuery } from '@tanstack/react-query';

import { bagsApi } from '@/api';

import type { BagDetail } from '@layapa/shared-types';

export function useBag(id: string | undefined, location: { lat: number; lng: number } | null) {
  return useQuery<BagDetail, Error>({
    queryKey: ['bags', 'detail', id, location?.lat, location?.lng],
    queryFn: () =>
      bagsApi.getBag(id as string, location ? { lat: location.lat, lng: location.lng } : {}),
    enabled: Boolean(id),
    staleTime: 60_000,
  });
}
