/**
 * Hook around expo-apple-authentication.
 *
 * Apple Sign In is iOS-only at the platform level. On Android / web the
 * `isAvailable` flag stays false and the button should be hidden.
 *
 * Returns the identity_token + optional fullName (which Apple only emits on
 * the very first sign-in for a given user — subsequent calls return null).
 */
import { useCallback, useEffect, useState } from 'react';
import { Platform } from 'react-native';
import * as AppleAuthentication from 'expo-apple-authentication';

export interface AppleSignInResult {
  identityToken: string;
  firstName: string;
  lastName: string;
}

export function useAppleSignIn() {
  const [isAvailable, setIsAvailable] = useState(false);

  useEffect(() => {
    if (Platform.OS !== 'ios') {
      setIsAvailable(false);
      return;
    }
    void AppleAuthentication.isAvailableAsync().then(setIsAvailable);
  }, []);

  const signIn = useCallback(async (): Promise<AppleSignInResult | null> => {
    try {
      const credential = await AppleAuthentication.signInAsync({
        requestedScopes: [
          AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
          AppleAuthentication.AppleAuthenticationScope.EMAIL,
        ],
      });
      if (!credential.identityToken) return null;
      return {
        identityToken: credential.identityToken,
        firstName: credential.fullName?.givenName ?? '',
        lastName: credential.fullName?.familyName ?? '',
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      // User-cancelled is the common case; don't treat it as an error.
      if (message.includes('ERR_REQUEST_CANCELED')) return null;
      console.warn('[apple] auth error', message);
      return null;
    }
  }, []);

  return { isAvailable, signIn };
}
