/**
 * Smoke test: business API wrappers build the right URLs/methods.
 */
import { businessApi } from '@/api';
import { __resetClientForTests, apiClient } from '@/api/client';

describe('businessApi', () => {
  let calls: { method: string; url: string; data?: unknown }[];
  // Save the original adapter once so we restore it after the suite.
  const originalAdapter = apiClient.defaults.adapter;

  beforeEach(() => {
    __resetClientForTests();
    calls = [];
    apiClient.defaults.adapter = (async (config: import('axios').InternalAxiosRequestConfig) => {
      const payload =
        typeof config.data === 'string'
          ? JSON.parse(config.data as string)
          : config.data instanceof FormData
            ? 'form-data'
            : undefined;
      calls.push({
        method: (config.method ?? 'get').toLowerCase(),
        url: config.url ?? '',
        data: payload,
      });
      return {
        data: [],
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    }) as never;
  });

  afterAll(() => {
    apiClient.defaults.adapter = originalAdapter;
  });

  it('listActiveOrders → GET /business/orders/active', async () => {
    await businessApi.listActiveOrders();
    expect(calls[0]).toEqual({
      method: 'get',
      url: '/business/orders/active',
      data: undefined,
    });
  });

  it('confirmPickupByScan → POST with qr_token', async () => {
    await businessApi.confirmPickupByScan({ qr_token: 'uuid-here' });
    expect(calls[0]).toEqual({
      method: 'post',
      url: '/business/orders/confirm-pickup-by-scan',
      data: { qr_token: 'uuid-here' },
    });
  });

  it('confirmPickupByPin → POST with business_location_id + pin', async () => {
    await businessApi.confirmPickupByPin({ business_location_id: 1, pin: '1234' });
    expect(calls[0]).toEqual({
      method: 'post',
      url: '/business/orders/confirm-pickup-by-pin',
      data: { business_location_id: 1, pin: '1234' },
    });
  });

  it('dispatchSuspended → POST with donation_id', async () => {
    await businessApi.dispatchSuspended({
      donation_id: 'd1',
      business_location_id: 2,
      notes: 'cliente recurrente',
    });
    expect(calls[0]).toEqual({
      method: 'post',
      url: '/business/suspended-meals/dispatch',
      data: { donation_id: 'd1', business_location_id: 2, notes: 'cliente recurrente' },
    });
  });

  it('submitOnboarding → POST multipart to onboarding endpoint', async () => {
    await businessApi.submitOnboarding({
      name: 'Pan del dia',
      business_type: 'bakery',
      tier: 'formal',
      location_name: 'Centro',
      address: 'Calle Larga',
      lat: -2.9,
      lng: -79,
      payout_method: 'bank_transfer',
      account_holder: 'Maria',
      bank_name: 'Pichincha',
      account_number: '123',
      cedula_number: '0102030405',
      food_safety_terms_accepted: true,
    });
    expect(calls[0]).toEqual({ method: 'post', url: '/business/onboarding', data: 'form-data' });
  });

  it('createBag → POST multipart to bags endpoint', async () => {
    await businessApi.createBag({
      business_location_id: 1,
      type: 'surprise',
      title: 'Pan sorpresa',
      original_price: '9.00',
      sale_price: '3.00',
      quantity_available: 5,
      pickup_window_start: '2026-06-12T18:00:00.000Z',
      pickup_window_end: '2026-06-12T20:00:00.000Z',
    });
    expect(calls[0]).toEqual({ method: 'post', url: '/business/bags', data: 'form-data' });
  });
});
