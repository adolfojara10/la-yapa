/** Auth store state transitions. */
/* eslint-disable import/first */

// Mock the api modules so the store doesn't try real HTTP. Must come before
// any import that pulls in @/auth/store (which itself imports @/api).
jest.mock('@/api', () => {
  const actual = jest.requireActual('@/api');
  return {
    ...actual,
    authApi: { logout: jest.fn(async () => {}) },
    usersApi: {
      getMe: jest.fn(),
      patchMe: jest.fn(),
    },
  };
});

import * as SecureStore from 'expo-secure-store';

import { usersApi } from '@/api';
import { __resetClientForTests } from '@/api/client';
import { useAuthStore } from '@/auth/store';
import { secureTokens } from '@/auth/secureStorage';

describe('useAuthStore', () => {
  beforeEach(() => {
    (SecureStore as unknown as { __reset: () => void }).__reset();
    secureTokens.__resetForTests();
    __resetClientForTests();
    useAuthStore.setState({ status: 'idle', user: null, tokens: null });
    jest.clearAllMocks();
  });

  it('starts in idle with no user', () => {
    const s = useAuthStore.getState();
    expect(s.status).toBe('idle');
    expect(s.user).toBeNull();
  });

  it('setAuthed persists tokens and flips status', async () => {
    const user = {
      id: 1,
      email: 'a@b.c',
      role: 'consumer',
      language: 'es',
      is_email_verified: true,
      is_premium: false,
      onboarding_completed: true,
      created_at: '',
      updated_at: '',
    } as never;
    await useAuthStore.getState().setAuthed(user, { access: 'A', refresh: 'R' });
    expect(useAuthStore.getState().status).toBe('authed');
    expect(await secureTokens.load()).toEqual({ access: 'A', refresh: 'R' });
  });

  it('hydrate with no stored tokens stays idle', async () => {
    await useAuthStore.getState().hydrate();
    expect(useAuthStore.getState().status).toBe('idle');
  });

  it('hydrate with stored tokens fetches /me and authenticates', async () => {
    await secureTokens.save({ access: 'A', refresh: 'R' });
    (usersApi.getMe as jest.Mock).mockResolvedValueOnce({
      id: 1,
      email: 'x@y.z',
      role: 'consumer',
      language: 'es',
      is_email_verified: true,
      is_premium: false,
      onboarding_completed: true,
    });
    await useAuthStore.getState().hydrate();
    expect(useAuthStore.getState().status).toBe('authed');
    expect(useAuthStore.getState().user?.email).toBe('x@y.z');
  });

  it('hydrate falls back to idle when /me fails (stale tokens)', async () => {
    await secureTokens.save({ access: 'A', refresh: 'R' });
    (usersApi.getMe as jest.Mock).mockRejectedValueOnce(new Error('401'));
    await useAuthStore.getState().hydrate();
    expect(useAuthStore.getState().status).toBe('idle');
    expect(await secureTokens.load()).toBeNull();
  });

  it('logout clears tokens and returns to idle', async () => {
    const user = {
      id: 1,
      email: 'a@b.c',
      role: 'consumer',
      language: 'es',
      is_email_verified: true,
      is_premium: false,
      onboarding_completed: true,
    } as never;
    await useAuthStore.getState().setAuthed(user, { access: 'A', refresh: 'R' });
    await useAuthStore.getState().logout();
    expect(useAuthStore.getState().status).toBe('idle');
    expect(await secureTokens.load()).toBeNull();
  });
});
