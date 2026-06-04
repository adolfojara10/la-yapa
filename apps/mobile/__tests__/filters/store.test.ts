import { useFilterStore } from '@/filters/store';

describe('useFilterStore', () => {
  beforeEach(() => {
    useFilterStore.getState().reset();
  });

  it('starts with defaults', () => {
    const s = useFilterStore.getState();
    expect(s.dietary).toEqual([]);
    expect(s.excludeAllergens).toEqual([]);
    expect(s.distanceKm).toBe(3);
    expect(s.sort).toBe('distance');
    expect(s.activeCount()).toBe(0);
  });

  it('toggleDietary adds + removes', () => {
    useFilterStore.getState().toggleDietary('vegan');
    expect(useFilterStore.getState().dietary).toEqual(['vegan']);
    useFilterStore.getState().toggleDietary('vegan');
    expect(useFilterStore.getState().dietary).toEqual([]);
  });

  it('activeCount counts each changed group once', () => {
    const s = useFilterStore.getState();
    s.toggleDietary('vegan');
    s.toggleAllergen('gluten');
    s.setDistance(10);
    s.setSort('price');
    expect(useFilterStore.getState().activeCount()).toBe(4);
  });

  it('toApiParams omits defaults but always sends radius and sort', () => {
    const params = useFilterStore.getState().toApiParams();
    expect(params).toEqual({ radius_km: 3, sort: 'distance' });
  });

  it('toApiParams serializes the full filter set', () => {
    const s = useFilterStore.getState();
    s.toggleDietary('vegan');
    s.toggleAllergen('gluten');
    s.setPrice({ min: 2, max: 6 });
    s.setPickupWindow('today');
    s.setMinRating(4);
    s.setSearchQuery('pan');
    const params = useFilterStore.getState().toApiParams();
    expect(params).toMatchObject({
      dietary: ['vegan'],
      exclude_allergens: ['gluten'],
      min_price: 2,
      max_price: 6,
      pickup_window: 'today',
      min_rating: 4,
      q: 'pan',
    });
  });

  it('reset returns to defaults', () => {
    useFilterStore.getState().toggleDietary('vegan');
    useFilterStore.getState().setDistance(10);
    useFilterStore.getState().reset();
    expect(useFilterStore.getState().activeCount()).toBe(0);
  });
});
