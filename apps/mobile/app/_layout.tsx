import 'react-native-gesture-handler';
import { Fraunces_700Bold, useFonts as useFraunces } from '@expo-google-fonts/fraunces';
import { Inter_400Regular, Inter_500Medium, useFonts as useInter } from '@expo-google-fonts/inter';
import {
  Poppins_600SemiBold,
  Poppins_700Bold,
  useFonts as usePoppins,
} from '@expo-google-fonts/poppins';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Slot, useRouter, useSegments } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useRef } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { useAuthStore, wireAuthCallbacks } from '@/auth/store';
import { ToastProvider } from '@/components/ui/Toast';
import { useRegisterPushToken } from '@/notifications/useRegisterPushToken';
import { ThemeProvider, useTheme } from '@/theme';

SplashScreen.preventAutoHideAsync().catch(() => null);

/**
 * Routing guard: snaps the user to the correct subtree based on auth state.
 *
 * Order of checks (first match wins):
 *   1. no tokens                → (auth)/welcome
 *   2. tokens but email unverified → (auth)/verify-email
 *   3. consumer + !onboarding   → (auth)/onboarding
 *   4. role = consumer          → (consumer)
 *   5. business_owner + no business   → (business)/onboarding
 *   6. business_owner + pending/rejected/suspended → (business)/status
 *   7. business_owner + approved      → (business)
 *   8. other roles                    → logout (mobile only supports the two above)
 *
 * Re-runs whenever (status, user, segments) change. The segments check
 * prevents an infinite loop: if we already match the target group, do nothing.
 */
function AuthGuard() {
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const segments = useSegments();
  const router = useRouter();
  const ranInitialNavigation = useRef(false);

  useEffect(() => {
    // Wait until hydrate() finishes; status === 'hydrating' = boot in progress.
    if (status === 'hydrating') return;

    const segmentsAny = segments as readonly string[];
    const inAuthGroup = segmentsAny[0] === '(auth)';
    const inConsumerGroup = segmentsAny[0] === '(consumer)';
    const inBusinessGroup = segmentsAny[0] === '(business)';
    const currentScreen = segmentsAny[1];

    if (status === 'idle') {
      // Allow forgot-password & reset-password screens to render without auth.
      if (!inAuthGroup) router.replace('/(auth)/welcome');
      return;
    }

    if (!user) return; // mid-transition, store about to populate

    if (!user.is_email_verified) {
      if (!(inAuthGroup && currentScreen === 'verify-email')) {
        router.replace('/(auth)/verify-email');
      }
      return;
    }

    if (user.role === 'consumer' && !user.onboarding_completed) {
      if (!(inAuthGroup && currentScreen === 'onboarding')) {
        router.replace('/(auth)/onboarding');
      }
      return;
    }

    if (user.role === 'consumer') {
      if (!inConsumerGroup) router.replace('/(consumer)/(tabs)');
      return;
    }
    if (user.role === 'business_owner') {
      const summary = user.business_summary;
      if (!summary) {
        if (!(inBusinessGroup && currentScreen === 'onboarding')) {
          router.replace('/(business)/onboarding');
        }
        return;
      }
      if (summary.status !== 'approved') {
        if (!(inBusinessGroup && currentScreen === 'status')) {
          router.replace('/(business)/status');
        }
        return;
      }
      if (!(inBusinessGroup && currentScreen !== 'onboarding' && currentScreen !== 'status')) {
        router.replace('/(business)/(tabs)');
      }
      return;
    }
    // admin / sales_rep should use the web admin; bounce them out.
    if (!ranInitialNavigation.current) {
      ranInitialNavigation.current = true;
      void logout();
    }
  }, [status, user, segments, router, logout]);

  return null;
}

function ThemedShell() {
  const { theme } = useTheme();
  // Registers the device's Expo push token with the backend once per
  // authed user. No-op when unauthed. Failures are swallowed; the app
  // continues to work without push if permission is denied.
  useRegisterPushToken();
  return (
    <>
      <StatusBar style={theme.mode === 'dark' ? 'light' : 'dark'} />
      <AuthGuard />
      <Slot />
    </>
  );
}

export default function RootLayout() {
  const [interLoaded] = useInter({ Inter_400Regular, Inter_500Medium });
  const [poppinsLoaded] = usePoppins({ Poppins_600SemiBold, Poppins_700Bold });
  const [frauncesLoaded] = useFraunces({ Fraunces_700Bold });

  const fontsReady = interLoaded && poppinsLoaded && frauncesLoaded;
  const hydrate = useAuthStore((s) => s.hydrate);

  useEffect(() => {
    wireAuthCallbacks();
    void hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (fontsReady) SplashScreen.hideAsync().catch(() => null);
  }, [fontsReady]);

  const queryClient = useMemo(() => new QueryClient(), []);

  if (!fontsReady) return null;

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <ThemeProvider>
          <QueryClientProvider client={queryClient}>
            <ToastProvider>
              <ThemedShell />
            </ToastProvider>
          </QueryClientProvider>
        </ThemeProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
