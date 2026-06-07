import { act, render, fireEvent } from '@testing-library/react-native';
import { createRef } from 'react';

import { PinEntrySheet, type PinSheetHandle } from '@/components/business/PinEntrySheet';
import { ThemeProvider } from '@/theme';

import type { BusinessOrder } from '@layapa/shared-types';

const fakeOrder: BusinessOrder = {
  id: 'o1',
  status: 'paid',
  quantity: 1,
  sale_price_snapshot: '4.50',
  total_paid: '4.50',
  pickup_code: '1234',
  payment_method: 'payphone',
  donate_as_suspended_meal: false,
  picked_up_at: null,
  created_at: '2026-06-04T10:00:00Z',
  consumer_first_name: 'Mateo',
  business_location_id: 42,
  business_location_name: 'Centro',
  bag: {
    id: 'b1',
    title: 'Bolsa #1',
    image_url: '',
    type: 'surprise',
    pickup_window_start: '2026-06-04T18:00:00Z',
    pickup_window_end: '2026-06-04T20:00:00Z',
    dietary_tags: [],
    allergen_warnings: [],
  },
  is_within_pickup_window: true,
  is_pin_locked: false,
};

function wrap(node: React.ReactElement) {
  return <ThemeProvider>{node}</ThemeProvider>;
}

describe('PinEntrySheet', () => {
  it('typing 4 digits enables submission with the active order location', () => {
    const onSubmit = jest.fn();
    const ref = createRef<PinSheetHandle>();
    const { getByLabelText, getByText } = render(
      wrap(<PinEntrySheet ref={ref} onSubmit={onSubmit} submitting={false} />),
    );
    // Open the sheet with the fake order.
    act(() => ref.current?.open([fakeOrder]));

    const otp = getByLabelText('Código de verificación');
    fireEvent.changeText(otp, '5678');

    const button = getByText('Confirmar retiro');
    fireEvent.press(button);
    expect(onSubmit).toHaveBeenCalledWith(42, '5678');
  });
});
