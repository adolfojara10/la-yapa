'use client';

import { create } from 'zustand';

import { fetchAdminSession, login as loginRequest, logout as logoutRequest } from '@/lib/admin-api';

import type { User } from '@layapa/shared-types';

type AuthStatus = 'idle' | 'hydrating' | 'authed';

interface AdminAuthState {
  status: AuthStatus;
  user: User | null;
  hydrate: () => Promise<void>;
  login: (payload: { email: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAdminAuthStore = create<AdminAuthState>((set) => ({
  status: 'hydrating',
  user: null,

  async hydrate() {
    set({ status: 'hydrating' });
    try {
      const user = await fetchAdminSession();
      if (user.role !== 'admin' && user.role !== 'sales_rep') {
        await logoutRequest();
        set({ status: 'idle', user: null });
        return;
      }
      set({ status: 'authed', user });
    } catch {
      set({ status: 'idle', user: null });
    }
  },

  async login(payload) {
    const response = await loginRequest(payload);
    if (response.user.role !== 'admin' && response.user.role !== 'sales_rep') {
      await logoutRequest();
      throw new Error('Tu cuenta no tiene acceso al panel admin.');
    }
    set({ status: 'authed', user: response.user });
  },

  async logout() {
    await logoutRequest();
    set({ status: 'idle', user: null });
  },
}));
