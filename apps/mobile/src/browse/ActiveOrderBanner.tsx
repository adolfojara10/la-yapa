/**
 * Pinned-at-top banner on Explorar when the consumer has an active order.
 * Tapping jumps to the order-detail screen — the "where's my pickup code?"
 * fast path.
 */
import { useRouter } from 'expo-router';
import { ChevronRight } from 'lucide-react-native';
import { Pressable, StyleSheet, View } from 'react-native';

import { OrderStatusBadge } from '@/components/order/OrderStatusBadge';
import { Text } from '@/components/ui/Text';
import { useActiveOrder } from '@/hooks/useActiveOrder';
import { useTheme } from '@/theme';

export function ActiveOrderBanner() {
  const { theme } = useTheme();
  const router = useRouter();
  const { order } = useActiveOrder();

  if (!order) return null;

  return (
    <Pressable
      onPress={() => router.push(`/(consumer)/orders/${order.id}`)}
      style={({ pressed }) => [
        styles.container,
        {
          backgroundColor: theme.colors.primarySoft,
          borderBottomColor: theme.colors.border,
          opacity: pressed ? 0.85 : 1,
        },
      ]}
    >
      <View style={{ flex: 1 }}>
        <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
          Pedido activo · {order.business_location.business_name}
        </Text>
        <View style={{ marginTop: 4, flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <OrderStatusBadge status={order.status} />
          <Text variant="small" style={{ color: theme.colors.textMuted }}>
            Código: {order.pickup_code}
          </Text>
        </View>
      </View>
      <ChevronRight size={20} color={theme.colors.text} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 12,
    borderBottomWidth: 1,
  },
});
