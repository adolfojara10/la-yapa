/**
 * QR scanner — vendor scans the consumer's pickup QR.
 *
 * The QR encodes the pickup_qr_token (a UUID). On scan we POST the token
 * to /business/orders/confirm-pickup-by-scan and navigate to the order
 * detail on success. The scanner is debounced via a ref so a single QR
 * doesn't trigger multiple POSTs while the camera resolves.
 *
 * Permission flow: prompt → granted → render CameraView. Denied → show
 * an instructional empty state with a "Abrir ajustes" link.
 */
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Linking from 'expo-linking';
import { useRouter } from 'expo-router';
import { useRef, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { businessApi } from '@/api';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useTheme } from '@/theme';

export default function ScanScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const toast = useToast();
  const [permission, requestPermission] = useCameraPermissions();
  const [submitting, setSubmitting] = useState(false);
  // Debounce: once we've sent a scan, ignore further scans until we get
  // either a response or the user backs out of the screen.
  const lockedRef = useRef(false);

  async function handleScanned(value: string) {
    if (lockedRef.current) return;
    lockedRef.current = true;
    setSubmitting(true);
    try {
      const order = await businessApi.confirmPickupByScan({ qr_token: value });
      toast.show({ title: '¡Pedido confirmado!', tone: 'success' });
      router.replace(`/(business)/orders/${order.id}`);
    } catch (err) {
      const detail = (err as { response?: { data?: { code?: string; detail?: string } } }).response
        ?.data;
      const code = detail?.code;
      if (code === 'qr_invalid') {
        toast.show({ title: 'QR no válido o ya usado.', tone: 'error' });
      } else if (code === 'outside_pickup_window') {
        toast.show({ title: 'Fuera de la ventana de retiro.', tone: 'warning' });
      } else if (code === 'pickup_invalid_status') {
        toast.show({ title: 'Este pedido no está pagado.', tone: 'warning' });
      } else {
        toast.show({ title: detail?.detail ?? 'No se pudo confirmar.', tone: 'error' });
      }
      // Release the lock so the vendor can try a different QR without
      // leaving + re-entering the screen.
      setTimeout(() => {
        lockedRef.current = false;
      }, 1500);
    } finally {
      setSubmitting(false);
    }
  }

  if (!permission) {
    // Permissions still loading.
    return (
      <SafeAreaView style={[styles.center, { backgroundColor: theme.colors.background }]}>
        <Text variant="body" style={{ color: theme.colors.textMuted }}>
          Solicitando permiso de cámara...
        </Text>
      </SafeAreaView>
    );
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={[styles.center, { backgroundColor: theme.colors.background }]}>
        <Text variant="h3" align="center" style={{ color: theme.colors.text }}>
          Necesitamos acceso a tu cámara
        </Text>
        <Text variant="body" align="center" style={{ color: theme.colors.textMuted, marginTop: 8 }}>
          Lo usamos solamente para escanear el código QR del pedido cuando el cliente lo retira.
        </Text>
        <View style={{ height: 16 }} />
        <Button variant="primary" size="lg" onPress={() => requestPermission()}>
          Permitir cámara
        </Button>
        <Pressable onPress={() => Linking.openSettings()} style={{ marginTop: 12 }}>
          <Text variant="small" style={{ color: theme.colors.primary, fontWeight: '600' }}>
            Abrir ajustes del sistema
          </Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  return (
    <View style={[styles.safe, { backgroundColor: '#000' }]}>
      <CameraView
        style={StyleSheet.absoluteFillObject}
        facing="back"
        barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
        onBarcodeScanned={({ data }) => handleScanned(data)}
      />
      <View pointerEvents="none" style={styles.overlay}>
        <View style={styles.reticle} />
        <Text variant="body" align="center" style={{ color: '#fff', marginTop: 24 }}>
          {submitting ? 'Confirmando...' : 'Apunta al QR del pedido'}
        </Text>
      </View>
      <SafeAreaView edges={['bottom']} style={styles.cancelWrap}>
        <Button variant="ghost" onPress={() => router.back()}>
          Cancelar
        </Button>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32 },
  overlay: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  reticle: {
    width: 240,
    height: 240,
    borderWidth: 3,
    borderColor: '#fff',
    borderRadius: 24,
  },
  cancelWrap: { position: 'absolute', bottom: 0, left: 0, right: 0, alignItems: 'center' },
});
