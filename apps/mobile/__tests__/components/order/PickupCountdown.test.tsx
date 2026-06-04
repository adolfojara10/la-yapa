import { render } from '@testing-library/react-native';

import { PickupCountdown } from '@/components/order/PickupCountdown';
import { ThemeProvider } from '@/theme';

function wrap(node: React.ReactElement) {
  return <ThemeProvider>{node}</ThemeProvider>;
}

describe('PickupCountdown', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2026-06-04T10:00:00Z'));
  });
  afterEach(() => {
    jest.useRealTimers();
  });

  it('shows "Abre en …" before the window starts', () => {
    const { getByText } = render(
      wrap(<PickupCountdown start="2026-06-04T11:30:00Z" end="2026-06-04T13:00:00Z" />),
    );
    expect(getByText(/Abre en 1h 30min/)).toBeTruthy();
  });

  it('shows "Cierra en …" during the window', () => {
    const { getByText } = render(
      wrap(<PickupCountdown start="2026-06-04T09:00:00Z" end="2026-06-04T11:00:00Z" />),
    );
    expect(getByText(/Cierra en/)).toBeTruthy();
  });

  it('shows "Ventana cerrada" after the window', () => {
    const { getByText } = render(
      wrap(<PickupCountdown start="2026-06-04T08:00:00Z" end="2026-06-04T09:00:00Z" />),
    );
    expect(getByText('Ventana cerrada')).toBeTruthy();
  });
});
