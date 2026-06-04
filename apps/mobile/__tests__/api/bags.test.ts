import { _internal } from '@/api/bags';

const { toQueryParams } = _internal;

describe('toQueryParams', () => {
  it('drops undefined and null', () => {
    expect(toQueryParams({ lat: undefined, lng: null as never, q: 'pan' })).toEqual({
      q: 'pan',
    });
  });

  it('serializes arrays as CSV', () => {
    expect(toQueryParams({ dietary: ['vegan', 'gluten_free'] })).toEqual({
      dietary: 'vegan,gluten_free',
    });
  });

  it('omits empty arrays', () => {
    expect(toQueryParams({ dietary: [], q: 'x' })).toEqual({ q: 'x' });
  });

  it('passes numbers through', () => {
    expect(toQueryParams({ lat: -2.9, lng: -79, radius_km: 3 })).toEqual({
      lat: -2.9,
      lng: -79,
      radius_km: 3,
    });
  });
});
