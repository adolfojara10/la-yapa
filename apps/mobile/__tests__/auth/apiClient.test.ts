/**
 * 401 → refresh → retry flow.
 *
 * Uses a tiny in-process HTTP recorder via axios's adapter, so we don't need
 * MSW or nock. Each test sets a custom adapter that returns the response we
 * want for a given URL+attempt count.
 */

import { __resetClientForTests, apiClient, onAuthFailure, setApiTokens } from '@/api/client';
import axios from 'axios';

type AdapterCall = (config: import('axios').InternalAxiosRequestConfig) => Promise<{
  data: unknown;
  status: number;
  statusText: string;
  headers: object;
  config: import('axios').InternalAxiosRequestConfig;
}>;

function withAdapter(adapter: AdapterCall) {
  apiClient.defaults.adapter = adapter as never;
}

describe('apiClient interceptors', () => {
  let postSpy: jest.SpyInstance;

  beforeEach(() => {
    __resetClientForTests();
    setApiTokens({ access: 'old-access', refresh: 'good-refresh' });
    postSpy = jest.spyOn(axios, 'post');
  });

  afterEach(() => {
    postSpy.mockRestore();
  });

  it('attaches Bearer header from in-memory access token', async () => {
    let observedAuth: string | undefined;
    withAdapter(async (config) => {
      observedAuth = config.headers?.Authorization as string;
      return { data: { ok: true }, status: 200, statusText: 'OK', headers: {}, config };
    });
    await apiClient.get('/things');
    expect(observedAuth).toBe('Bearer old-access');
  });

  it('on 401, refreshes once and retries the original request', async () => {
    postSpy.mockResolvedValueOnce({ data: { access: 'new-access' } });

    let attempts = 0;
    withAdapter(async (config) => {
      attempts += 1;
      if (attempts === 1) {
        const err: import('axios').AxiosError = Object.assign(new Error('401'), {
          isAxiosError: true,
          config,
          response: {
            data: {},
            status: 401,
            statusText: 'Unauthorized',
            headers: {},
            config,
          },
          name: 'AxiosError',
          message: '401',
          toJSON: () => ({}),
        }) as never;
        throw err;
      }
      return {
        data: { retried: true, auth: config.headers?.Authorization },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    });

    const response = await apiClient.get('/things');
    expect(response.data).toEqual({ retried: true, auth: 'Bearer new-access' });
    expect(postSpy).toHaveBeenCalledTimes(1);
    expect(postSpy).toHaveBeenCalledWith(
      expect.stringContaining('/auth/refresh'),
      { refresh: 'good-refresh' },
      expect.any(Object),
    );
  });

  it('on failed refresh, triggers onAuthFailure and rejects', async () => {
    postSpy.mockRejectedValueOnce(new Error('refresh-failed'));
    const onFail = jest.fn();
    onAuthFailure(onFail);

    withAdapter(async (config) => {
      const err: import('axios').AxiosError = Object.assign(new Error('401'), {
        isAxiosError: true,
        config,
        response: {
          data: {},
          status: 401,
          statusText: 'Unauthorized',
          headers: {},
          config,
        },
        name: 'AxiosError',
        message: '401',
        toJSON: () => ({}),
      }) as never;
      throw err;
    });

    await expect(apiClient.get('/things')).rejects.toBeDefined();
    expect(onFail).toHaveBeenCalledTimes(1);
  });
});
