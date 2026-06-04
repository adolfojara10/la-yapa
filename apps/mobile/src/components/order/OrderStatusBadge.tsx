import { StyleSheet, View } from 'react-native';

import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';

import type { OrderStatus } from '@layapa/shared-types';

const LABELS: Record<OrderStatus, string> = {
  pending_payment: 'Pago pendiente',
  paid: 'Pagado',
  ready_for_pickup: 'Listo para retirar',
  completed: 'Completado',
  pending_refund: 'Reembolso en proceso',
  cancelled: 'Cancelado',
  refunded: 'Reembolsado',
  expired: 'Expirado',
};

interface Props {
  status: OrderStatus;
}

export function OrderStatusBadge({ status }: Props) {
  const { theme } = useTheme();

  const palette: Record<OrderStatus, { bg: string; fg: string }> = {
    pending_payment: { bg: theme.colors.warningSoft, fg: theme.colors.warning },
    paid: { bg: theme.colors.primarySoft, fg: theme.colors.primary },
    ready_for_pickup: { bg: theme.colors.primarySoft, fg: theme.colors.primary },
    completed: { bg: theme.colors.successSoft, fg: theme.colors.success },
    pending_refund: { bg: theme.colors.warningSoft, fg: theme.colors.warning },
    cancelled: { bg: theme.colors.errorSoft, fg: theme.colors.error },
    refunded: { bg: theme.colors.surfaceMuted, fg: theme.colors.textMuted },
    expired: { bg: theme.colors.surfaceMuted, fg: theme.colors.textMuted },
  };
  const { bg, fg } = palette[status];

  return (
    <View style={[styles.badge, { backgroundColor: bg, borderRadius: theme.radii.full }]}>
      <Text variant="small" style={{ color: fg, fontWeight: '700' }}>
        {LABELS[status]}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
});
