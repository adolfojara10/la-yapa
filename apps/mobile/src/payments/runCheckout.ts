/**
 * Provider-agnostic checkout dispatcher.
 *
 * Input: a `ChargeSessionResponse` from `POST /payments/charge`.
 * Output: one of 'completed_in_webview' | 'cancelled' | 'failed'.
 *
 * The webhook is authoritative regardless of what we return here — the
 * caller polls `/orders/{id}` to read the real status after this resolves.
 * We never claim "success" from the client side; the best we can say is
 * "the user finished the WebView flow" or "they backed out".
 *
 * Phase 2 forward-compat: when PayPhone (and later Stripe) ship native SDKs,
 * `session.sdk_payload` will be populated; we dispatch to a native module
 * here. Today both providers return `webview_url` only.
 */
import * as WebBrowser from 'expo-web-browser';

import type { ChargeSessionResponse } from '@layapa/shared-types';

export type CheckoutResult = 'completed_in_webview' | 'cancelled' | 'failed';

export async function runCheckout(
  session: ChargeSessionResponse,
  options: { returnUrl: string },
): Promise<CheckoutResult> {
  // sdk_payload branch reserved for Phase 2 native-SDK migration.
  // Today this never fires; left here so the call site stays stable when
  // PayPhone / Stripe SDKs land.
  if (session.sdk_payload && Object.keys(session.sdk_payload).length > 0) {
    return runNativeSdkCheckout(session);
  }
  if (!session.webview_url) return 'failed';

  try {
    const result = await WebBrowser.openAuthSessionAsync(session.webview_url, options.returnUrl);
    if (result.type === 'success') return 'completed_in_webview';
    if (result.type === 'cancel' || result.type === 'dismiss') return 'cancelled';
    return 'failed';
  } catch {
    return 'failed';
  }
}

async function runNativeSdkCheckout(_session: ChargeSessionResponse): Promise<CheckoutResult> {
  // Intentionally not implemented — see AGENTS.md §4 "Payment provider
  // roadmap (Phase 2)". When a provider starts returning sdk_payload, this
  // function dispatches to the appropriate native module:
  //
  //   if (session.provider === 'payphone') return runPayPhoneSdk(session);
  //   if (session.provider === 'stripe')   return runStripeSdk(session);
  //
  // For now, no provider ships SDK payloads; this code path is unreachable.
  return 'failed';
}
