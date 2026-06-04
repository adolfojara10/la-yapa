/**
 * Order detail — QR + PIN + countdown + cancel.
 *
 * Polls the order until status is terminal (see useOrder), so after a
 * webview payment succeeds, the screen flips from "Esperando confirmación"
 * to showing the QR within ~2s of the webhook firing.
 */
import * as Linking from 'expo-linking';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ordersApi } from '@/api';
import { OrderStatusBadge } from '@/components/order/OrderStatusBadge';
import { PickupCountdown } from '@/components/order/PickupCountdown';
import { PickupQrCode } from '@/components/order/PickupQrCode';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useOrder } from '@/hooks/useOrder';
import { useTheme } from '@/theme';

export default function OrderDetailScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const toast = useToast();
  const { id } = useLocalSearchParams<{ id: string }>();
  const query = useOrder(id);
  const [cancelling, setCancelling] = useState(false);

  async function handleCancel() {
    if (!id || !query.data) return;
    Alert.alert(
      '¿Cancelar pedido?',
      query.data.status === 'paid'
        ? 'Tu reembolso se procesará en 1–3 días hábiles.'
        : 'Esta acción no se puede deshacer.',
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Sí, cancelar',
          style: 'destructive',
          onPress: async () => {
            setCancelling(true);
            try {
              await ordersApi.cancelOrder(String(id));
              await query.refetch();
            } catch (err) {
              const detail = (err as { response?: { data?: { code?: string } } }).response?.data
                ?.code;
              if (detail === 'cancellation_outside_window') {
                toast.show({
                  title: 'Ya pasó la ventana de cancelación (1h antes del retiro).',
                  tone: 'error',
                });
              } else {
                toast.show({ title: 'No pudimos cancelar el pedido.', tone: 'error' });
              }
            } finally {
              setCancelling(false);
            }
          },
        },
      ],
    );
  }

  function handleDirections() {
    const loc = query.data?.business_location;
    if (!loc?.latitude || !loc?.longitude) return;
    Linking.openURL(`https://www.google.com/maps?q=${loc.latitude},${loc.longitude}`).catch(
      () => {},
    );
  }

  if (query.isLoading || !query.data) {
    return (
      <SafeAreaView style={[styles.center, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator color={theme.colors.primary} />
      </SafeAreaView>
    );
  }

  const order = query.data;
  const isPaid = order.status === 'paid' || order.status === 'ready_for_pickup';
  const isAwaitingPayment = order.status === 'pending_payment';
  const isRefundPending = order.status === 'pending_refund';

  return (
    <SafeAreaView
      edges={['bottom']}
      style={[styles.safe, { backgroundColor: theme.colors.background }]}
    >
      <ScrollView contentContainerStyle={styles.scroll}>
        <OrderStatusBadge status={order.status} />

        <Text variant="h2" style={{ color: theme.colors.text, marginTop: 8 }}>
          {order.business_location.business_name}
        </Text>
        <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
          {order.bag.title}
        </Text>

        {isPaid ? (
          <>
            <View style={styles.qrBlock}>
              <PickupQrCode qrToken={order.pickup_qr_token} pickupCode={order.pickup_code} />
            </View>
            <View
              style={[
                styles.windowRow,
                { borderColor: theme.colors.border, borderRadius: theme.radii.md },
              ]}
            >
              <Text variant="small" style={{ color: theme.colors.textMuted }}>
                Ventana de retiro
              </Text>
              <Text variant="bodyStrong" style={{ color: theme.colors.text, marginTop: 4 }}>
                {new Date(order.bag.pickup_window_start).toLocaleTimeString('es-EC', {
                  hour: 'numeric',
                  minute: '2-digit',
                  hour12: false,
                })}
                {' – '}
                {new Date(order.bag.pickup_window_end).toLocaleTimeString('es-EC', {
                  hour: 'numeric',
                  minute: '2-digit',
                  hour12: false,
                })}
              </Text>
              <View style={{ marginTop: 6 }}>
                <PickupCountdown
                  start={order.bag.pickup_window_start}
                  end={order.bag.pickup_window_end}
                />
              </View>
            </View>
          </>
        ) : null}

        {isAwaitingPayment ? (
          <View
            style={[
              styles.pendingBox,
              { backgroundColor: theme.colors.warningSoft, borderRadius: theme.radii.md },
            ]}
          >
            <Text variant="bodyStrong" style={{ color: theme.colors.warning }}>
              Esperando confirmación de pago
            </Text>
            <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
              Si pagaste hace más de 2 minutos y aún no se confirma, contacta soporte.
            </Text>
          </View>
        ) : null}

        {isRefundPending ? (
          <View
            style={[
              styles.pendingBox,
              { backgroundColor: theme.colors.warningSoft, borderRadius: theme.radii.md },
            ]}
          >
            <Text variant="bodyStrong" style={{ color: theme.colors.warning }}>
              Reembolso en proceso
            </Text>
            <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
              Tu dinero volverá a tu tarjeta en 1–3 días hábiles.
            </Text>
          </View>
        ) : null}

        <Pressable
          onPress={handleDirections}
          style={[
            styles.locationBlock,
            { borderColor: theme.colors.border, borderRadius: theme.radii.md },
          ]}
        >
          <Text variant="small" style={{ color: theme.colors.textMuted }}>
            Lugar de retiro
          </Text>
          <Text variant="bodyStrong" style={{ color: theme.colors.text, marginTop: 4 }}>
            {order.business_location.name}
          </Text>
          <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 2 }}>
            {order.business_location.address}
          </Text>
          {order.business_location.latitude && order.business_location.longitude ? (
            <Text
              variant="small"
              style={{ color: theme.colors.primary, marginTop: 8, fontWeight: '600' }}
            >
              Cómo llegar →
            </Text>
          ) : null}
        </Pressable>

        <View style={styles.totalsRow}>
          <Text variant="small" style={{ color: theme.colors.textMuted }}>
            Total pagado
          </Text>
          <Text variant="h3" style={{ color: theme.colors.primary }}>
            ${order.total_paid}
          </Text>
        </View>

        {order.is_within_consumer_cancel_window &&
        !['cancelled', 'refunded', 'expired', 'completed', 'pending_refund'].includes(
          order.status,
        ) ? (
          <Button variant="ghost" fullWidth loading={cancelling} onPress={handleCancel}>
            Cancelar pedido
          </Button>
        ) : null}

        <Button variant="ghost" fullWidth onPress={() => router.replace('/(consumer)/(tabs)')}>
          Volver al inicio
        </Button>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { padding: 16, gap: 16 },
  qrBlock: { alignItems: 'center', marginTop: 12 },
  windowRow: { padding: 12, borderWidth: 1 },
  pendingBox: { padding: 16 },
  locationBlock: { padding: 12, borderWidth: 1 },
  totalsRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    paddingHorizontal: 4,
  },
});
