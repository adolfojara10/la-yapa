/**
 * Auth store — single source of truth for the routing guard.
 *
 * Lifecycle:
 *   hydrate()  → load tokens from SecureStore on app boot, then fetch /users/me
 *   register / login / loginWithGoogle / loginWithApple → set tokens + user
 *   refreshMe() → re-fetch /users/me after PATCH or email verification
 *   logout()   → blacklist refresh server-side, clear local state
 *
 * Status state machine:
 *   'idle'        no tokens, show welcome
 *   'hydrating'   app just booted, checking SecureStore
 *   'authed'      tokens valid, user object loaded
 */
import { create } from 'zustand';

import { authApi, onAuthFailure, onTokensRotated, setApiTokens, usersApi } from '@/api';
import { secureTokens } from './secureStorage';

import type { AuthTokens, User } from '@layapa/shared-types';

export type AuthStatus = 'idle' | 'hydrating' | 'authed';

interface AuthState {
  status: AuthStatus;
  user: User | null;
  tokens: AuthTokens | null;

  hydrate: () => Promise<void>;
  setAuthed: (user: User, tokens: AuthTokens) => Promise<void>;
  refreshMe: () => Promise<User | null>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  status: 'idle',
  user: null,
  tokens: null,

  async hydrate() {
    set({ status: 'hydrating' });
    const tokens = await secureTokens.load();
    if (!tokens) {
      set({ status: 'idle' });
      return;
    }
    setApiTokens(tokens);
    try {
      const user = await usersApi.getMe();
      set({ status: 'authed', user, tokens });
    } catch {
      // Tokens are stale / refresh failed. Treat as logged out.
      await secureTokens.clear();
      setApiTokens(null);
      set({ status: 'idle', user: null, tokens: null });
    }
  },

  async setAuthed(user, tokens) {
    setApiTokens(tokens);
    await secureTokens.save(tokens);
    set({ status: 'authed', user, tokens });
  },

  async refreshMe() {
    if (get().status !== 'authed') return null;
    try {
      const user = await usersApi.getMe();
      set({ user });
      return user;
    } catch {
      return null;
    }
  },

  async logout() {
    const { tokens } = get();
    if (tokens?.refresh) {
      try {
        await authApi.logout({ refresh: tokens.refresh });
      } catch {
        // Swallow — we still want local logout to succeed.
      }
    }
    await secureTokens.clear();
    setApiTokens(null);
    set({ status: 'idle', user: null, tokens: null });
  },
}));

// Wire the API client's interceptor callbacks into the store. Called once
// from the root layout when the app boots.
let wired = false;
export function wireAuthCallbacks(): void {
  if (wired) return;
  wired = true;
  onAuthFailure(() => {
    void useAuthStore.getState().logout();
  });
  onTokensRotated((tokens) => {
    const state = useAuthStore.getState();
    if (state.status === 'authed') {
      void secureTokens.save(tokens);
      useAuthStore.setState({ tokens });
    }
  });
}
