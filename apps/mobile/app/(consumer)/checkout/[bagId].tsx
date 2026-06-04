/**
 * Checkout screen — last stop before the user lands in a payment WebView.
 *
 * Flow:
 *   1. Render order summary (bag, qty, pickup window, total).
 *   2. User picks payment method (PayPhone | DeUna).
 *   3. Optional: donate-as-suspended-meal toggle.
 *   4. Terms acceptance gate.
 *   5. Tap pay → POST /consumer/orders (creates pending order)
 *               → POST /payments/charge (gets webview_url)
 *               → runCheckout (opens WebView)
 *               → router.replace to order detail (which polls until paid)
 *
 * Webhook is authoritative — the order-detail screen polls until status
 * flips to paid (or shows an error if WebView was cancelled mid-flow).
 */
import { Image } from 'expo-image';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as Linking from 'expo-linking';
import { Check } from 'lucide-react-native';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Switch, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ordersApi, paymentsApi } from '@/api';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useBag } from '@/hooks/useBag';
import { useUserLocation } from '@/hooks/useUserLocation';
import { runCheckout } from '@/payments/runCheckout';
import { useTheme } from '@/theme';

import type { ProviderName } from '@layapa/shared-types';

function formatWindow(start?: string, end?: string): string {
  if (!start || !end) return '';
  const s = new Date(start);
  const e = new Date(end);
  const fmt = (d: Date) =>
    d.toLocaleTimeString('es-EC', { hour: 'numeric', minute: '2-digit', hour12: false });
  return `${fmt(s)} – ${fmt(e)}`;
}

export default function CheckoutScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const toast = useToast();
  const { bagId } = useLocalSearchParams<{ bagId: string }>();
  const { location } = useUserLocation();
  const bagQuery = useBag(bagId, location);

  const [provider, setProvider] = useState<ProviderName>('payphone');
  const [quantity] = useState(1);
  const [donate, setDonate] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const bag = bagQuery.data;
  const subtotal = bag ? Number(bag.sale_price) * quantity : 0;
  const total = subtotal; // no taxes yet; SRI invoicing is its own session

  async function handlePay() {
    if (!bagId || !termsAccepted) return;
    setSubmitting(true);
    try {
      const order = await ordersApi.createOrder({
        bag_id: String(bagId),
        quantity,
        donate_as_suspended_meal: donate,
      });
      const returnUrl = Linking.createURL('payment-result', {
        queryParams: { order_id: order.id },
      });
      const session = await paymentsApi.createCharge({
        order_id: order.id,
        provider,
        return_url: returnUrl,
      });
      const result = await runCheckout(session, { returnUrl });
      // The order screen polls until the webhook flips status. We navigate
      // there regardless of WebView outcome — if it's still pending, the
      // user can retry from there; if cancelled, they see a clear state.
      router.replace(`/(consumer)/orders/${order.id}`);
      if (result === 'cancelled') {
        toast.show({
          title: 'Pago cancelado. Tu pedido sigue reservado por 15 min.',
          tone: 'warning',
        });
      } else if (result === 'failed') {
        toast.show({ title: 'Algo falló con el pago. Intenta de nuevo.', tone: 'error' });
      }
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string; code?: string } } }).response
        ?.data;
      const code = detail?.code;
      if (code === 'insufficient_stock') {
        toast.show({ title: 'Esta bolsa se acaba de agotar.', tone: 'error' });
      } else {
        toast.show({ title: detail?.detail ?? 'No pudimos procesar el pedido.', tone: 'error' });
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (bagQuery.isLoading || !bag) {
    return (
      <SafeAreaView style={[styles.center, { backgroundColor: theme.colors.background }]}>
        <Text variant="body" style={{ color: theme.colors.textMuted }}>
          Cargando...
        </Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView
      edges={['bottom']}
      style={[styles.safe, { backgroundColor: theme.colors.background }]}
    >
      <ScrollView contentContainerStyle={styles.scroll}>
        <Section label="Resumen" theme={theme}>
          <View style={styles.summaryRow}>
            <Image
              source={{ uri: bag.image_url }}
              style={[styles.summaryImage, { borderRadius: theme.radii.md }]}
              contentFit="cover"
            />
            <View style={{ flex: 1 }}>
              <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
                {bag.business.name}
              </Text>
              <Text variant="small" style={{ color: theme.colors.textMuted }}>
                {bag.title}
              </Text>
              <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
                Retiro: {formatWindow(bag.pickup_window_start, bag.pickup_window_end)}
              </Text>
            </View>
          </View>
        </Section>

        <Section label="Método de pago" theme={theme}>
          <View style={styles.methodRow}>
            <MethodButton
              active={provider === 'payphone'}
              label="Tarjeta · PayPhone"
              onPress={() => setProvider('payphone')}
            />
            <MethodButton
              active={provider === 'de_una'}
              label="DeUna"
              onPress={() => setProvider('de_una')}
            />
          </View>
        </Section>

        <Section label="Comunidad" theme={theme}>
          <View style={styles.toggleRow}>
            <View style={{ flex: 1 }}>
              <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
                Donar como comida suspendida
              </Text>
              <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
                Tu bolsa se entrega a alguien que la necesita. El negocio sirve la comida; tú no la
                retiras.
              </Text>
            </View>
            <Switch
              value={donate}
              onValueChange={setDonate}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
            />
          </View>
        </Section>

        <Pressable onPress={() => setTermsAccepted((v) => !v)} style={styles.termsRow}>
          <View
            style={[
              styles.checkbox,
              {
                borderColor: termsAccepted ? theme.colors.primary : theme.colors.border,
                backgroundColor: termsAccepted ? theme.colors.primary : 'transparent',
                borderRadius: theme.radii.sm,
              },
            ]}
          >
            {termsAccepted ? <Check size={14} color={theme.colors.textInverse} /> : null}
          </View>
          <Text variant="small" style={{ color: theme.colors.textMuted, flex: 1 }}>
            Acepto los términos del retiro y la política de cancelación (cancelable hasta 1 hora
            antes del inicio de la ventana de retiro).
          </Text>
        </Pressable>
      </ScrollView>

      <View
        style={[
          styles.footer,
          { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.border },
        ]}
      >
        <View style={styles.totalRow}>
          <Text variant="small" style={{ color: theme.colors.textMuted }}>
            Total
          </Text>
          <Text variant="h2" style={{ color: theme.colors.primary }}>
            ${total.toFixed(2)}
          </Text>
        </View>
        <Button
          variant="primary"
          size="lg"
          fullWidth
          disabled={!termsAccepted}
          loading={submitting}
          onPress={handlePay}
        >
          Pagar ${total.toFixed(2)}
        </Button>
      </View>
    </SafeAreaView>
  );
}

function Section({
  label,
  theme,
  children,
}: {
  label: string;
  theme: ReturnType<typeof useTheme>['theme'];
  children: React.ReactNode;
}) {
  return (
    <View style={styles.section}>
      <Text variant="small" style={{ color: theme.colors.textMuted, marginBottom: 8 }}>
        {label.toUpperCase()}
      </Text>
      {children}
    </View>
  );
}

function MethodButton({
  active,
  label,
  onPress,
}: {
  active: boolean;
  label: string;
  onPress: () => void;
}) {
  const { theme } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.methodButton,
        {
          borderColor: active ? theme.colors.primary : theme.colors.border,
          backgroundColor: active ? theme.colors.primarySoft : theme.colors.surface,
          borderRadius: theme.radii.md,
        },
      ]}
    >
      <Text
        variant="bodyStrong"
        style={{ color: active ? theme.colors.primary : theme.colors.text }}
      >
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { padding: 16, gap: 8, paddingBottom: 32 },
  section: { marginBottom: 16 },
  summaryRow: { flexDirection: 'row', gap: 12 },
  summaryImage: { width: 80, height: 80 },
  methodRow: { gap: 8 },
  methodButton: {
    padding: 16,
    borderWidth: 1.5,
    alignItems: 'flex-start',
  },
  toggleRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  termsRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 8 },
  checkbox: {
    width: 22,
    height: 22,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  footer: { padding: 16, borderTopWidth: 1, gap: 12 },
  totalRow: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between' },
});
