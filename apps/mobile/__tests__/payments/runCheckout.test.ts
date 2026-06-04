/**
 * runCheckout dispatcher: webview path + sdk path + failure modes.
 */
import * as WebBrowser from 'expo-web-browser';

import { runCheckout } from '@/payments/runCheckout';

import type { ChargeSessionResponse } from '@layapa/shared-types';

const baseSession: ChargeSessionResponse = {
  session_id: 's1',
  provider: 'payphone',
  webview_url: 'https://fake.layapa.test/checkout/abc',
  sdk_payload: {},
  amount: '4.50',
  currency: 'USD',
  transaction_id: 1,
};

describe('runCheckout', () => {
  beforeEach(() => {
    (WebBrowser.openAuthSessionAsync as jest.Mock).mockReset();
  });

  it('opens the webview when sdk_payload is empty', async () => {
    (WebBrowser.openAuthSessionAsync as jest.Mock).mockResolvedValueOnce({ type: 'success' });
    const result = await runCheckout(baseSession, { returnUrl: 'layapa://payment-result' });
    expect(WebBrowser.openAuthSessionAsync).toHaveBeenCalledWith(
      baseSession.webview_url,
      'layapa://payment-result',
    );
    expect(result).toBe('completed_in_webview');
  });

  it('returns cancelled when the user dismisses the webview', async () => {
    (WebBrowser.openAuthSessionAsync as jest.Mock).mockResolvedValueOnce({ type: 'cancel' });
    expect(await runCheckout(baseSession, { returnUrl: 'x' })).toBe('cancelled');

    (WebBrowser.openAuthSessionAsync as jest.Mock).mockResolvedValueOnce({ type: 'dismiss' });
    expect(await runCheckout(baseSession, { returnUrl: 'x' })).toBe('cancelled');
  });

  it('returns failed when the webview throws', async () => {
    (WebBrowser.openAuthSessionAsync as jest.Mock).mockRejectedValueOnce(new Error('boom'));
    expect(await runCheckout(baseSession, { returnUrl: 'x' })).toBe('failed');
  });

  it('returns failed when both webview_url and sdk_payload are empty', async () => {
    const empty: ChargeSessionResponse = { ...baseSession, webview_url: '' };
    expect(await runCheckout(empty, { returnUrl: 'x' })).toBe('failed');
    expect(WebBrowser.openAuthSessionAsync).not.toHaveBeenCalled();
  });

  it('routes to native SDK when sdk_payload is populated (Phase 2 path)', async () => {
    const withSdk: ChargeSessionResponse = {
      ...baseSession,
      sdk_payload: { token: 'sdk-token' },
    };
    // The native SDK path is intentionally unimplemented this session — it
    // returns 'failed' so the screen surfaces an actionable error rather
    // than hanging.
    expect(await runCheckout(withSdk, { returnUrl: 'x' })).toBe('failed');
    expect(WebBrowser.openAuthSessionAsync).not.toHaveBeenCalled();
  });
});
