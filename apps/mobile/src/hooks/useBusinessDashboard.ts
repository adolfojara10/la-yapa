import { useQuery } from '@tanstack/react-query';

import { businessApi } from '@/api';

import type { BusinessDashboardSummary } from '@layapa/shared-types';

export function useBusinessDashboard() {
  return useQuery<BusinessDashboardSummary, Error>({
    queryKey: ['business', 'dashboard'],
    queryFn: () => businessApi.getDashboard(),
    refetchInterval: 30_000,
    staleTime: 0,
  });
}
