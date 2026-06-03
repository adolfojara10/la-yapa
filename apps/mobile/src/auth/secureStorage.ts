/**
 * Tiny wrapper around `expo-secure-store` for the two JWT keys.
 *
 * Why not AsyncStorage: it's plaintext on disk and unsuitable for refresh
 * tokens. Why a wrapper at all: we want a single place to add fallbacks
 * (web `localStorage`, in-memory for Jest) without sprinkling Platform
 * checks across the auth flow.
 */
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

const ACCESS_KEY = 'layapa.auth.access';
const REFRESH_KEY = 'layapa.auth.refresh';

const memoryFallback = new Map<string, string>();

const useFallback = Platform.OS === 'web';

async function setItem(key: string, value: string): Promise<void> {
  if (useFallback) {
    memoryFallback.set(key, value);
    return;
  }
  await SecureStore.setItemAsync(key, value, {
    keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY,
  });
}

async function getItem(key: string): Promise<string | null> {
  if (useFallback) {
    return memoryFallback.get(key) ?? null;
  }
  return (await SecureStore.getItemAsync(key)) ?? null;
}

async function deleteItem(key: string): Promise<void> {
  if (useFallback) {
    memoryFallback.delete(key);
    return;
  }
  await SecureStore.deleteItemAsync(key);
}

export const secureTokens = {
  async save(tokens: { access: string; refresh: string }): Promise<void> {
    await Promise.all([setItem(ACCESS_KEY, tokens.access), setItem(REFRESH_KEY, tokens.refresh)]);
  },
  async load(): Promise<{ access: string; refresh: string } | null> {
    const [access, refresh] = await Promise.all([getItem(ACCESS_KEY), getItem(REFRESH_KEY)]);
    if (!access || !refresh) return null;
    return { access, refresh };
  },
  async clear(): Promise<void> {
    await Promise.all([deleteItem(ACCESS_KEY), deleteItem(REFRESH_KEY)]);
  },
  // Test-only: clears the in-memory fallback. No-op on native.
  __resetForTests(): void {
    memoryFallback.clear();
  },
};
