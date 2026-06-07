import { apiClient } from './client';

export interface RegisterPushTokenPayload {
  token: string;
  platform: 'ios' | 'android';
}

export interface RegisteredPushToken {
  id: number;
  token: string;
  platform: 'ios' | 'android';
  is_active: boolean;
  created_at: string;
}

export async function registerPushToken(
  payload: RegisterPushTokenPayload,
): Promise<RegisteredPushToken> {
  const { data } = await apiClient.post<RegisteredPushToken>(
    '/notifications/register-token',
    payload,
  );
  return data;
}
