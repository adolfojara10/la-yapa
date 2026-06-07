import { useQuery } from '@tanstack/react-query';

import { businessApi } from '@/api';

import type { SuspendedMealForDispatch } from '@layapa/shared-types';

export function useSuspendedMeals() {
  return useQuery<SuspendedMealForDispatch[], Error>({
    queryKey: ['business', 'suspended', 'active'],
    queryFn: () => businessApi.listActiveSuspended(),
    refetchInterval: 30_000,
    staleTime: 0,
  });
}
