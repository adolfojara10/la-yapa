import { render } from '@testing-library/react-native';

import { OrderStatusBadge } from '@/components/order/OrderStatusBadge';
import { ThemeProvider } from '@/theme';

function wrap(node: React.ReactElement) {
  return <ThemeProvider>{node}</ThemeProvider>;
}

describe('OrderStatusBadge', () => {
  it.each([
    ['pending_payment', 'Pago pendiente'],
    ['paid', 'Pagado'],
    ['pending_refund', 'Reembolso en proceso'],
    ['cancelled', 'Cancelado'],
    ['refunded', 'Reembolsado'],
    ['completed', 'Completado'],
  ] as const)('renders the label for status=%s', (status, label) => {
    const { getByText } = render(wrap(<OrderStatusBadge status={status} />));
    expect(getByText(label)).toBeTruthy();
  });
});
