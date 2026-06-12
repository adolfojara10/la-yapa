/**
 * Business dashboard — active orders worklist + pickup-confirmation actions.
 *
 * Header: today's counts (active orders / completed today / suspended-meals
 * available). Suspended count is a subtle badge — full list lives in the
 * Suspendidas tab.
 *
 * Action row: "Escanear QR" → opens the scanner modal. "Ingresar PIN" →
 * opens a bottom sheet with the OTP input (reused from auth's email-verify
 * screen).
 *
 * Below: active orders grouped chronologically. Tap a row → order detail.
 */
import { useRouter } from 'expo-router';
import { BarChart3, KeyRound, Plus, QrCode } from 'lucide-react-native';
import { useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { businessApi } from '@/api';
import { OrderStatusBadge } from '@/components/order/OrderStatusBadge';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useBusinessActiveOrders } from '@/hooks/useBusinessOrders';
import { useBusinessDashboard } from '@/hooks/useBusinessDashboard';
import { useTheme } from '@/theme';

import { PinEntrySheet, type PinSheetHandle } from '@/components/business/PinEntrySheet';

import type { BusinessOrder } from '@layapa/shared-types';

function formatWindow(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const fmt = (d: Date) =>
    d.toLocaleTimeString('es-EC', { hour: 'numeric', minute: '2-digit', hour12: false });
  return `${fmt(s)}–${fmt(e)}`;
}

function greetingForHour() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Buenos dias';
  if (hour < 19) return 'Buenas tardes';
  return 'Buenas noches';
}

export default function BusinessDashboard() {
  const { theme } = useTheme();
  const router = useRouter();
  const toast = useToast();
  const dashboard = useBusinessDashboard();
  const orders = useBusinessActiveOrders();
  const pinSheetRef = useRef<PinSheetHandle>(null);
  const [pinSubmitting, setPinSubmitting] = useState(false);

  const summary = dashboard.data;

  async function handlePinSubmit(locationId: number, pin: string) {
    setPinSubmitting(true);
    try {
      const order = await businessApi.confirmPickupByPin({
        business_location_id: locationId,
        pin,
      });
      pinSheetRef.current?.close();
      toast.show({ title: '¡Pedido confirmado!', tone: 'success' });
      await Promise.all([orders.refetch(), dashboard.refetch()]);
      router.push(`/(business)/orders/${order.id}`);
    } catch (err) {
      const detail = (err as { response?: { data?: { code?: string; detail?: string } } }).response
        ?.data;
      const code = detail?.code;
      if (code === 'pin_invalid') {
        toast.show({ title: 'PIN incorrecto.', tone: 'error' });
      } else if (code === 'pin_locked') {
        toast.show({ title: 'PIN bloqueado — usa el QR.', tone: 'error' });
      } else if (code === 'outside_pickup_window') {
        toast.show({ title: 'Fuera de la ventana de retiro.', tone: 'warning' });
      } else {
        toast.show({ title: detail?.detail ?? 'Error al confirmar.', tone: 'error' });
      }
    } finally {
      setPinSubmitting(false);
    }
  }

  return (
    <SafeAreaView
      edges={['top']}
      style={[styles.safe, { backgroundColor: theme.colors.background }]}
    >
      <FlatList<BusinessOrder>
        data={orders.data ?? []}
        keyExtractor={(o) => o.id}
        refreshControl={
          <RefreshControl
            refreshing={orders.isRefetching && !orders.isLoading}
            onRefresh={() => {
              orders.refetch();
              dashboard.refetch();
            }}
            tintColor={theme.colors.primary}
          />
        }
        ListHeaderComponent={
          <View>
            <View style={styles.header}>
              <Text variant="h2" style={{ color: theme.colors.text }}>
                {greetingForHour()}, Yapi te acompana hoy
              </Text>
              {summary ? (
                <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
                  {summary.today_orders_count} pedidos · ${summary.today_revenue} en ingresos ·{' '}
                  {summary.today_bags_sold} bolsas vendidas
                  {summary.suspended_meals_available > 0
                    ? ` · ${summary.suspended_meals_available} suspendidas disponibles`
                    : ''}
                </Text>
              ) : null}
            </View>

            <View style={styles.actionsRow}>
              <View style={{ flex: 1 }}>
                <Button
                  variant="primary"
                  size="lg"
                  fullWidth
                  leftIcon={<Plus size={18} color={theme.colors.textInverse} />}
                  onPress={() => router.push('/(business)/bags/new')}
                >
                  Nueva bolsa
                </Button>
              </View>
              <View style={{ flex: 1 }}>
                <Button
                  variant="secondary"
                  size="lg"
                  fullWidth
                  leftIcon={<QrCode size={18} color={theme.colors.textInverse} />}
                  onPress={() => router.push('/(business)/orders')}
                >
                  Ver pedidos
                </Button>
              </View>
            </View>

            <View style={styles.actionsRow}>
              <View style={{ flex: 1 }}>
                <Button
                  variant="ghost"
                  size="lg"
                  fullWidth
                  leftIcon={<QrCode size={18} color={theme.colors.text} />}
                  onPress={() => router.push('/(business)/orders/scan')}
                >
                  Escanear QR
                </Button>
              </View>
              <View style={{ flex: 1 }}>
                <Button
                  variant="ghost"
                  size="lg"
                  fullWidth
                  leftIcon={<KeyRound size={18} color={theme.colors.text} />}
                  onPress={() => pinSheetRef.current?.open(orders.data ?? [])}
                >
                  Ingresar PIN
                </Button>
              </View>
            </View>

            <View style={styles.actionsRow}>
              <View style={{ flex: 1 }}>
                <Button
                  variant="ghost"
                  size="lg"
                  fullWidth
                  leftIcon={<BarChart3 size={18} color={theme.colors.text} />}
                  onPress={() => router.push('/(business)/analytics')}
                >
                  Analytics
                </Button>
              </View>
            </View>

            <Text
              variant="bodyStrong"
              style={{ color: theme.colors.text, marginTop: 16, marginHorizontal: 16 }}
            >
              Próximos retiros
            </Text>
          </View>
        }
        renderItem={({ item }) => (
          <Pressable
            onPress={() => router.push(`/(business)/orders/${item.id}`)}
            style={({ pressed }) => [
              styles.row,
              {
                backgroundColor: theme.colors.surface,
                borderColor: theme.colors.border,
                borderRadius: theme.radii.lg,
                opacity: pressed ? 0.85 : 1,
              },
            ]}
          >
            <View style={{ flex: 1 }}>
              <Text variant="bodyStrong" numberOfLines={1} style={{ color: theme.colors.text }}>
                {item.consumer_first_name} · {item.quantity} bolsa{item.quantity > 1 ? 's' : ''}
              </Text>
              <Text variant="small" numberOfLines={1} style={{ color: theme.colors.textMuted }}>
                {item.bag.title}
              </Text>
              <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
                {formatWindow(item.bag.pickup_window_start, item.bag.pickup_window_end)}
              </Text>
            </View>
            <View style={styles.rowRight}>
              <Text variant="h3" style={{ color: theme.colors.primary }}>
                {item.pickup_code}
              </Text>
              <OrderStatusBadge status={item.status} />
            </View>
          </Pressable>
        )}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          orders.isLoading ? (
            <View style={styles.centerSlot}>
              <ActivityIndicator color={theme.colors.primary} />
            </View>
          ) : (
            <View style={styles.centerSlot}>
              <Text variant="body" align="center" style={{ color: theme.colors.textMuted }}>
                No tienes pedidos activos en este momento.
              </Text>
            </View>
          )
        }
      />

      <PinEntrySheet ref={pinSheetRef} onSubmit={handlePinSubmit} submitting={pinSubmitting} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  header: { padding: 16, paddingBottom: 8 },
  actionsRow: { flexDirection: 'row', gap: 12, paddingHorizontal: 16, marginTop: 12 },
  list: { paddingBottom: 32, gap: 8 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginHorizontal: 16,
    marginTop: 12,
    borderWidth: 1,
  },
  rowRight: { alignItems: 'flex-end', gap: 6 },
  centerSlot: { padding: 32, alignItems: 'center' },
});
