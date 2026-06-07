/**
 * Registers the device's Expo push token with the backend.
 *
 * Called once from `app/_layout.tsx` after auth hydrates. Idempotent on
 * the server side (update_or_create on the token string), so re-running
 * on every cold start is fine — it just refreshes the row's user/platform.
 *
 * Permission flow:
 *   - On Android the permission is granted at install time → just fetch token.
 *   - On iOS we request runtime permission via `requestPermissionsAsync`.
 *   - If denied, we silently skip; no crash, no user-facing complaint.
 *     The consumer's profile screen could surface a "habilitar
 *     notificaciones" affordance later (Phase 2).
 *
 * In dev (Expo Go is not used — see AGENTS.md §2), the token is the
 * device's real Expo token from the dev client. In tests we mock
 * expo-notifications entirely in jest.setup.js.
 */
import { useEffect, useRef } from 'react';
import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';

import { notificationsApi } from '@/api';
import { useAuthStore } from '@/auth/store';

export function useRegisterPushToken() {
  const status = useAuthStore((s) => s.status);
  const ranForUserId = useRef<number | null>(null);

  useEffect(() => {
    if (status !== 'authed') return;
    const user = useAuthStore.getState().user;
    if (!user) return;
    if (ranForUserId.current === user.id) return;
    ranForUserId.current = user.id;

    void registerOnce();
  }, [status]);
}

async function registerOnce() {
  try {
    const { status: existing } = await Notifications.getPermissionsAsync();
    let granted = existing === 'granted';
    if (!granted) {
      const requested = await Notifications.requestPermissionsAsync();
      granted = requested.status === 'granted';
    }
    if (!granted) {
      // Permission denied. Skip silently; future call to this hook (next
      // cold start) will re-prompt on iOS.
      return;
    }

    const token = await Notifications.getExpoPushTokenAsync();
    if (!token?.data) return;

    const platform: 'ios' | 'android' = Platform.OS === 'ios' ? 'ios' : 'android';
    await notificationsApi.registerPushToken({ token: token.data, platform });
  } catch (err) {
    // Never block the app on a notification-registration failure.
    // eslint-disable-next-line no-console
    console.warn('[push] register failed', err);
  }
}
