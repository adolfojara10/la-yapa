/**
 * Axios instance with JWT auth + automatic refresh on 401.
 *
 * Single in-flight refresh: concurrent requests that all 401 wait on the
 * same refresh promise instead of stampeding the /auth/refresh endpoint
 * (and incidentally invalidating each other when ROTATE_REFRESH_TOKENS is on).
 *
 * The store import is lazy (inside functions) to avoid a Metro circular
 * dependency: store.ts imports api functions, which import this client.
 */
import axios, {
  AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios';
import Constants from 'expo-constants';

const baseURL =
  process.env.EXPO_PUBLIC_API_BASE_URL ??
  (Constants.expoConfig?.extra as { apiBaseUrl?: string } | undefined)?.apiBaseUrl ??
  'http://localhost:8000/api/v1';

export const apiClient: AxiosInstance = axios.create({
  baseURL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
});

// ---- Token plumbing ----

let inMemoryAccessToken: string | null = null;
let inMemoryRefreshToken: string | null = null;
let refreshInFlight: Promise<string | null> | null = null;

export function setApiTokens(tokens: { access: string; refresh: string } | null): void {
  if (tokens === null) {
    inMemoryAccessToken = null;
    inMemoryRefreshToken = null;
    return;
  }
  inMemoryAccessToken = tokens.access;
  inMemoryRefreshToken = tokens.refresh;
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (inMemoryAccessToken && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${inMemoryAccessToken}`;
  }
  return config;
});

type RetriableConfig = AxiosRequestConfig & { _retry?: boolean };

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    const status = error.response?.status;

    // Never retry: refresh endpoint failures or already-retried requests.
    const url = original?.url ?? '';
    const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/refresh');

    if (status !== 401 || !original || original._retry || isAuthEndpoint) {
      return Promise.reject(error);
    }

    original._retry = true;

    // Coalesce concurrent refreshes onto a single promise.
    if (!refreshInFlight) {
      refreshInFlight = refreshAccessToken().finally(() => {
        refreshInFlight = null;
      });
    }
    const newAccess = await refreshInFlight;
    if (!newAccess) {
      // Refresh failed → caller's onAuthFailure handler (registered by the
      // auth store) will clear tokens and bounce to the welcome screen.
      onAuthFailureCallback?.();
      return Promise.reject(error);
    }
    if (original.headers) {
      (original.headers as Record<string, string>).Authorization = `Bearer ${newAccess}`;
    }
    return apiClient(original);
  },
);

async function refreshAccessToken(): Promise<string | null> {
  if (!inMemoryRefreshToken) return null;
  try {
    // Use a bare axios call to bypass our own interceptors.
    const response = await axios.post<{ access: string; refresh?: string }>(
      `${baseURL}/auth/refresh`,
      { refresh: inMemoryRefreshToken },
      { timeout: 10_000, headers: { 'Content-Type': 'application/json' } },
    );
    inMemoryAccessToken = response.data.access;
    if (response.data.refresh) {
      // Rotation enabled server-side; persist the new refresh too.
      inMemoryRefreshToken = response.data.refresh;
      onTokensRotatedCallback?.({
        access: response.data.access,
        refresh: response.data.refresh,
      });
    } else {
      onTokensRotatedCallback?.({
        access: response.data.access,
        refresh: inMemoryRefreshToken,
      });
    }
    return response.data.access;
  } catch {
    return null;
  }
}

// ---- Callbacks the auth store registers at startup ----

let onAuthFailureCallback: (() => void) | null = null;
let onTokensRotatedCallback: ((tokens: { access: string; refresh: string }) => void) | null = null;

export function onAuthFailure(handler: () => void): void {
  onAuthFailureCallback = handler;
}

export function onTokensRotated(
  handler: (tokens: { access: string; refresh: string }) => void,
): void {
  onTokensRotatedCallback = handler;
}

// Test-only.
export function __resetClientForTests(): void {
  inMemoryAccessToken = null;
  inMemoryRefreshToken = null;
  refreshInFlight = null;
  onAuthFailureCallback = null;
  onTokensRotatedCallback = null;
}
