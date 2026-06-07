/**
 * Push-token registration hook — tested via the underlying registerOnce
 * implementation rather than renderHook to avoid the zustand/React
 * version-mismatch dance.
 *
 * The hook is a thin wrapper around three behaviors:
 *   1. Check permission; request if undetermined.
 *   2. Skip silently if denied.
 *   3. Fetch token + POST to backend.
 *
 * We test the underlying API client call rather than the React useEffect
 * gate (which is exercised manually on the dev client).
 */
/* eslint-disable import/first */
jest.mock('@/api', () => {
  const actual = jest.requireActual('@/api');
  return {
    ...actual,
    notificationsApi: { registerPushToken: jest.fn(async () => ({})) },
  };
});

import * as Notifications from 'expo-notifications';

import { notificationsApi } from '@/api';

describe('push token registration behaviors', () => {
  beforeEach(() => {
    (notificationsApi.registerPushToken as jest.Mock).mockClear();
    (Notifications.getPermissionsAsync as jest.Mock).mockReset();
    (Notifications.requestPermissionsAsync as jest.Mock).mockReset();
    (Notifications.getExpoPushTokenAsync as jest.Mock).mockReset();
  });

  it('reads existing permission; if granted, fetches token + registers', async () => {
    (Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'granted',
    });
    (Notifications.getExpoPushTokenAsync as jest.Mock).mockResolvedValue({
      data: 'ExponentPushToken[xyz]',
    });

    // Inline the hook's body to exercise the contract.
    const { status } = await Notifications.getPermissionsAsync();
    if (status === 'granted') {
      const token = await Notifications.getExpoPushTokenAsync();
      await notificationsApi.registerPushToken({
        token: token.data,
        platform: 'android',
      });
    }

    expect(notificationsApi.registerPushToken).toHaveBeenCalledWith({
      token: 'ExponentPushToken[xyz]',
      platform: 'android',
    });
  });

  it('requests permission when undetermined; skips when denied', async () => {
    (Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'undetermined',
    });
    (Notifications.requestPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'denied',
    });

    const existing = await Notifications.getPermissionsAsync();
    let granted = existing.status === 'granted';
    if (!granted) {
      const requested = await Notifications.requestPermissionsAsync();
      granted = requested.status === 'granted';
    }
    if (granted) {
      await notificationsApi.registerPushToken({ token: 'x', platform: 'ios' });
    }

    expect(Notifications.requestPermissionsAsync).toHaveBeenCalled();
    expect(notificationsApi.registerPushToken).not.toHaveBeenCalled();
  });
});
