import { buildTheme, type Theme, type ThemeMode } from '@layapa/ui';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { useColorScheme } from 'react-native';

type ThemePreference = ThemeMode | 'system';

interface ThemeContextValue {
  theme: Theme;
  mode: ThemeMode;
  preference: ThemePreference;
  setPreference: (pref: ThemePreference) => void;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

interface ThemeProviderProps {
  children: ReactNode;
  /** Force a specific mode (used in tests and the in-app design-system route). */
  forceMode?: ThemeMode;
  /** Initial user preference; defaults to system. */
  initialPreference?: ThemePreference;
}

export function ThemeProvider({
  children,
  forceMode,
  initialPreference = 'system',
}: ThemeProviderProps) {
  const systemScheme = useColorScheme();
  const [preference, setPreferenceState] = useState<ThemePreference>(initialPreference);

  // Keep RN's reported scheme in state so changes (settings → dark) propagate.
  const [resolved, setResolved] = useState<ThemeMode>(
    forceMode ?? (systemScheme === 'dark' ? 'dark' : 'light'),
  );

  useEffect(() => {
    if (forceMode) {
      setResolved(forceMode);
      return;
    }
    if (preference === 'system') {
      setResolved(systemScheme === 'dark' ? 'dark' : 'light');
    } else {
      setResolved(preference);
    }
  }, [forceMode, preference, systemScheme]);

  const setPreference = useCallback((pref: ThemePreference) => setPreferenceState(pref), []);
  const toggle = useCallback(() => setResolved((m) => (m === 'dark' ? 'light' : 'dark')), []);

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme: buildTheme(resolved),
      mode: resolved,
      preference,
      setPreference,
      toggle,
    }),
    [resolved, preference, setPreference, toggle],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useTheme must be used inside <ThemeProvider>');
  }
  return ctx;
}
