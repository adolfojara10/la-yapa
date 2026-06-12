import { useQuery } from '@tanstack/react-query';

import { businessApi } from '@/api';

import type { BagTemplate, BusinessLocation, ManagedBag } from '@layapa/shared-types';

export function useBusinessLocations() {
  return useQuery<BusinessLocation[], Error>({
    queryKey: ['business-locations'],
    queryFn: () => businessApi.listLocations(),
  });
}

export function useBusinessBags() {
  return useQuery<ManagedBag[], Error>({
    queryKey: ['business-bags'],
    queryFn: () => businessApi.listBags(),
  });
}

export function useManagedBag(id: string | undefined) {
  return useQuery<ManagedBag, Error>({
    queryKey: ['business-bag', id],
    enabled: Boolean(id),
    queryFn: () => businessApi.getManagedBag(id as string),
  });
}

export function useBagTemplates() {
  return useQuery<BagTemplate[], Error>({
    queryKey: ['business-bag-templates'],
    queryFn: () => businessApi.listBagTemplates(),
  });
}
