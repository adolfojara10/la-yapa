/**
 * Business order detail — read-only summary + "Confirmar retiro" CTA that
 * triggers PIN entry (vendor types the consumer's 4-digit code).
 *
 * Already-completed orders show a static success badge instead of the CTA.
 */
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useRef, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { businessApi } from '@/api';
import { PinEntrySheet, type PinSheetHandle } from '@/components/business/PinEntrySheet';
import { OrderStatusBadge } from '@/components/order/OrderStatusBadge';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useBusinessOrder } from '@/hooks/useBusinessOrders';
import { useTheme } from '@/theme';

function formatWindow(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const fmt = (d: Date) =>
    d.toLocaleTimeString('es-EC', { hour: 'numeric', minute: '2-digit', hour12: false });
  return `${fmt(s)} – ${fmt(e)}`;
}

export default function BusinessOrderDetail() {
  const { theme } = useTheme();
  const router = useRouter();
  const toast = useToast();
  const { id } = useLocalSearchParams<{ id: string }>();
  const query = useBusinessOrder(id);
  const pinSheetRef = useRef<PinSheetHandle>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handlePinSubmit(locationId: number, pin: string) {
    setSubmitting(true);
    try {
      await businessApi.confirmPickupByPin({
        business_location_id: locationId,
        pin,
      });
      pinSheetRef.current?.close();
      toast.show({ title: '¡Pedido confirmado!', tone: 'success' });
      await query.refetch();
    } catch (err) {
      const detail = (err as { response?: { data?: { code?: string; detail?: string } } }).response
        ?.data;
      if (detail?.code === 'pin_invalid') {
        toast.show({ title: 'PIN incorrecto.', tone: 'error' });
      } else if (detail?.code === 'pin_locked') {
        toast.show({ title: 'PIN bloqueado — usa el QR.', tone: 'error' });
      } else if (detail?.code === 'outside_pickup_window') {
        toast.show({ title: 'Fuera de la ventana.', tone: 'warning' });
      } else {
        toast.show({ title: detail?.detail ?? 'Error al confirmar.', tone: 'error' });
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (query.isLoading || !query.data) {
    return (
      <SafeAreaView style={[styles.center, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator color={theme.colors.primary} />
      </SafeAreaView>
    );
  }

  const order = query.data;
  const canConfirm = order.status === 'paid' || order.status === 'ready_for_pickup';

  return (
    <SafeAreaView
      edges={['bottom']}
      style={[styles.safe, { backgroundColor: theme.colors.background }]}
    >
      <ScrollView contentContainerStyle={styles.scroll}>
        <OrderStatusBadge status={order.status} />

        <Text variant="h1" style={{ color: theme.colors.primary, marginTop: 12 }}>
          {order.pickup_code}
        </Text>
        <Text variant="small" style={{ color: theme.colors.textMuted }}>
          Código de retiro
        </Text>

        <View style={[styles.divider, { backgroundColor: theme.colors.border }]} />

        <Section label="Cliente">
          <Text variant="h3" style={{ color: theme.colors.text }}>
            {order.consumer_first_name}
          </Text>
          <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
            {order.quantity} bolsa{order.quantity > 1 ? 's' : ''} · ${order.total_paid}
          </Text>
        </Section>

        <Section label="Bolsa">
          <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
            {order.bag.title}
          </Text>
          <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
            Retiro: {formatWindow(order.bag.pickup_window_start, order.bag.pickup_window_end)}
          </Text>
          {order.bag.dietary_tags.length > 0 ? (
            <View style={styles.chipRow}>
              {order.bag.dietary_tags.map((tag) => (
                <Chip key={tag} label={tag} tone="primary" />
              ))}
            </View>
          ) : null}
          {order.bag.allergen_warnings.length > 0 ? (
            <View>
              <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 12 }}>
                Alérgenos
              </Text>
              <View style={styles.chipRow}>
                {order.bag.allergen_warnings.map((tag) => (
                  <Chip key={tag} label={tag} tone="error" />
                ))}
              </View>
            </View>
          ) : null}
        </Section>

        {order.donate_as_suspended_meal ? (
          <View
            style={[
              styles.donationBanner,
              {
                backgroundColor: theme.colors.primarySoft,
                borderRadius: theme.radii.md,
              },
            ]}
          >
            <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
              Bolsa donada como comida suspendida
            </Text>
            <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
              Este pedido fue donado por el cliente. La bolsa debe servirse a alguien que la
              necesite — no espera retiro por parte del cliente.
            </Text>
          </View>
        ) : null}

        {canConfirm ? (
          <Button
            variant="primary"
            size="lg"
            fullWidth
            onPress={() => pinSheetRef.current?.open([order])}
          >
            Confirmar con PIN
          </Button>
        ) : null}

        {canConfirm ? (
          <Button
            variant="secondary"
            size="lg"
            fullWidth
            onPress={() => router.push('/(business)/orders/scan')}
          >
            Escanear QR del cliente
          </Button>
        ) : null}
      </ScrollView>

      <PinEntrySheet ref={pinSheetRef} onSubmit={handlePinSubmit} submitting={submitting} />
    </SafeAreaView>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  const { theme } = useTheme();
  return (
    <View style={styles.section}>
      <Text variant="small" style={{ color: theme.colors.textMuted, marginBottom: 6 }}>
        {label.toUpperCase()}
      </Text>
      {children}
    </View>
  );
}

function Chip({ label, tone }: { label: string; tone: 'primary' | 'error' }) {
  const { theme } = useTheme();
  const bg = tone === 'error' ? theme.colors.errorSoft : theme.colors.primarySoft;
  return (
    <View style={[styles.chip, { backgroundColor: bg, borderRadius: theme.radii.full }]}>
      <Text variant="small" style={{ color: theme.colors.text, fontWeight: '600' }}>
        {label.replace(/_/g, ' ')}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { padding: 16, gap: 12, paddingBottom: 32 },
  divider: { height: 1, marginVertical: 12 },
  section: { marginVertical: 8 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  chip: { paddingVertical: 6, paddingHorizontal: 12 },
  donationBanner: { padding: 12 },
});
