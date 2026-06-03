import { apiClient } from './client';

import type { UpdateMePayload, User } from '@layapa/shared-types';

export async function getMe(): Promise<User> {
  const { data } = await apiClient.get<User>('/users/me');
  return data;
}

export async function patchMe(payload: UpdateMePayload): Promise<User> {
  const { data } = await apiClient.patch<User>('/users/me', payload);
  return data;
}
