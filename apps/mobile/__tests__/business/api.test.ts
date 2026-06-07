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
      calls.push({
        method: (config.method ?? 'get').toLowerCase(),
        url: config.url ?? '',
        data: config.data ? JSON.parse(config.data as string) : undefined,
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
});
