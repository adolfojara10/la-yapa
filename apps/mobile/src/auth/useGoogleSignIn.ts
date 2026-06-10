/**
 * Hook around expo-auth-session for Google sign-in.
 *
 * Returns an async `signIn()` that resolves with the Google id_token, which
 * the caller exchanges with our backend (`POST /auth/google`).
 *
 * Setup gotcha: Google Cloud Console must be configured with the EXACT
 * client IDs we pass here, OR the redirect lands on Google's "this app is
 * blocked" page. See AGENTS.md §4 "Provisioning social auth credentials".
 */
import { useCallback, useEffect } from 'react';
import * as AuthSession from 'expo-auth-session';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';

WebBrowser.maybeCompleteAuthSession();

export function useGoogleSignIn() {
  const [, response, promptAsync] = Google.useIdTokenAuthRequest({
    iosClientId: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID || 'dummy-ios-client-id',
    androidClientId: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID || 'dummy-android-client-id',
    webClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID || 'dummy-web-client-id',
  });

  // Surface unexpected provider errors (e.g. account chooser dismissed) for callers.
  useEffect(() => {
    if (response?.type === 'error') {
      // Logged via console; the screen-level handler will show a Toast.
      console.warn('[google] auth error', response.error);
    }
  }, [response]);

  const signIn = useCallback(async (): Promise<string | null> => {
    const result = await promptAsync();
    if (result.type !== 'success') return null;
    // useIdTokenAuthRequest returns the id_token directly in params.
    const idToken =
      (result as AuthSession.AuthSessionResult & { params?: { id_token?: string } }).params
        ?.id_token ?? null;
    return idToken;
  }, [promptAsync]);

  return { signIn };
}
