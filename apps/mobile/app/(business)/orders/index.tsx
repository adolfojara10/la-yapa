import { useRouter } from 'expo-router';
import { RefreshControl, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { OrderStatusBadge } from '@/components/order/OrderStatusBadge';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useBusinessActiveOrders, useBusinessTodayOrders } from '@/hooks/useBusinessOrders';
import { useTheme } from '@/theme';

import type { BusinessOrder } from '@layapa/shared-types';

function formatWindow(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const fmt = (d: Date) =>
    d.toLocaleTimeString('es-EC', { hour: 'numeric', minute: '2-digit', hour12: false });
  return `${fmt(s)}–${fmt(e)}`;
}

function OrderCard({
  order,
  onPress,
  history = false,
}: {
  order: BusinessOrder;
  onPress: () => void;
  history?: boolean;
}) {
  const { theme } = useTheme();

  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: theme.colors.surface,
          borderColor: theme.colors.border,
          borderRadius: theme.radii.lg,
        },
      ]}
    >
      <View style={styles.cardHeader}>
        <View style={{ flex: 1 }}>
          <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
            {order.consumer_first_name} · {order.quantity} bolsa{order.quantity > 1 ? 's' : ''}
          </Text>
          <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
            {order.bag.title}
          </Text>
          <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
            {order.business_location_name} ·{' '}
            {formatWindow(order.bag.pickup_window_start, order.bag.pickup_window_end)}
          </Text>
        </View>
        <View style={{ alignItems: 'flex-end', gap: 6 }}>
          <Text variant="bodyStrong" style={{ color: theme.colors.primary }}>
            ${order.total_paid}
          </Text>
          <OrderStatusBadge status={order.status} />
        </View>
      </View>

      <Button variant={history ? 'ghost' : 'secondary'} fullWidth onPress={onPress}>
        {history ? 'Ver detalle' : 'Gestionar pedido'}
      </Button>
    </View>
  );
}

export default function BusinessOrdersScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const active = useBusinessActiveOrders();
  const history = useBusinessTodayOrders();

  const refreshing = active.isRefetching || history.isRefetching;

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              active.refetch();
              history.refetch();
            }}
            tintColor={theme.colors.primary}
          />
        }
      >
        <View style={styles.section}>
          <Text variant="h2" style={{ color: theme.colors.text }}>
            Pedidos activos
          </Text>
          <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
            Confirma retiros y revisa la ventana de pickup de cada pedido.
          </Text>
          {active.data?.length ? (
            active.data.map((order) => (
              <OrderCard
                key={order.id}
                order={order}
                onPress={() => router.push(`/(business)/orders/${order.id}`)}
              />
            ))
          ) : (
            <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 12 }}>
              No tienes pedidos activos ahora mismo.
            </Text>
          )}
        </View>

        <View style={styles.section}>
          <Text variant="h3" style={{ color: theme.colors.text }}>
            Historial de hoy
          </Text>
          {history.data?.length ? (
            history.data.map((order) => (
              <OrderCard
                key={order.id}
                order={order}
                history
                onPress={() => router.push(`/(business)/orders/${order.id}`)}
              />
            ))
          ) : (
            <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 12 }}>
              Aun no hay pedidos cerrados hoy.
            </Text>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  content: { padding: 16, gap: 20, paddingBottom: 32 },
  section: { gap: 12 },
  card: { padding: 16, borderWidth: 1, gap: 12 },
  cardHeader: { flexDirection: 'row', gap: 12 },
});
