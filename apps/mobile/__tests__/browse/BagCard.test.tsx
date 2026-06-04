import { render } from '@testing-library/react-native';

import { BagCard } from '@/browse/BagCard';
import { ThemeProvider } from '@/theme';

import type { BagListItem } from '@layapa/shared-types';

const bag: BagListItem = {
  id: 'b1',
  title: 'Bolsa Sorpresa',
  type: 'surprise',
  image_url: 'https://example.com/img.jpg',
  original_price: '12.00',
  sale_price: '4.50',
  discount_percent: 62,
  quantity_available: 5,
  pickup_window_start: '2026-06-04T18:00:00Z',
  pickup_window_end: '2026-06-04T20:00:00Z',
  business: {
    id: 1,
    location_id: 10,
    name: 'Panadería La Esperanza',
    logo_url: '',
    address: 'Calle Larga 4-12',
    latitude: -2.9001,
    longitude: -79.0059,
    rating_average: 4.6,
    rating_count: 23,
  },
  distance_m: 612,
  is_favorited: false,
  dietary_tags: ['vegan'],
  allergen_warnings: [],
};

function wrap(node: React.ReactElement) {
  return <ThemeProvider>{node}</ThemeProvider>;
}

describe('BagCard', () => {
  it('renders business + bag title + prices + discount + distance', () => {
    const { getByText, getAllByText } = render(wrap(<BagCard bag={bag} onPress={() => {}} />));
    expect(getByText('Panadería La Esperanza')).toBeTruthy();
    expect(getByText('Bolsa Sorpresa')).toBeTruthy();
    expect(getByText('$4.50')).toBeTruthy();
    expect(getByText('$12.00')).toBeTruthy();
    expect(getByText('-62%')).toBeTruthy();
    expect(getByText(/612 m/)).toBeTruthy();
    // Rating block
    expect(getAllByText(/4\.6/).length).toBeGreaterThan(0);
  });

  it('falls back to "Sin reseñas" when no rating', () => {
    const noRating: BagListItem = {
      ...bag,
      business: { ...bag.business, rating_average: null, rating_count: 0 },
    };
    const { getByText } = render(wrap(<BagCard bag={noRating} onPress={() => {}} />));
    expect(getByText('Sin reseñas')).toBeTruthy();
  });
});
