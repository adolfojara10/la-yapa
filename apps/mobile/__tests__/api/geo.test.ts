import { searchPlaces } from '@/api/geo';
import { apiClient } from '@/api/client';

jest.mock('@/api/client', () => ({
  apiClient: {
    get: jest.fn(),
  },
}));

describe('searchPlaces', () => {
  it('returns geo suggestions from the backend proxy response', async () => {
    const results = [{ id: '1', label: 'Cuenca, Azuay, Ecuador', lat: -2.9, lng: -79.0 }];
    (apiClient.get as jest.Mock).mockResolvedValue({ data: { results } });

    await expect(searchPlaces({ q: 'cuenca', country: 'ec' })).resolves.toEqual(results);
    expect(apiClient.get).toHaveBeenCalledWith('/geo/search', {
      params: { q: 'cuenca', country: 'ec' },
    });
  });
});
