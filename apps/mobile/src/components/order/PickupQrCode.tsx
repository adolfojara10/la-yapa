/**
 * QR code that encodes the pickup_qr_token. Scanned by the business app to
 * confirm pickup. PIN (pickup_code) renders alongside as a fallback for
 * businesses without scanners.
 */
import QRCode from 'react-native-qrcode-svg';
import { StyleSheet, View } from 'react-native';

import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';

interface Props {
  qrToken: string;
  pickupCode: string;
  /** Visual size of the QR. Defaults to 220 — large enough to scan from a phone screen. */
  size?: number;
}

export function PickupQrCode({ qrToken, pickupCode, size = 220 }: Props) {
  const { theme } = useTheme();
  return (
    <View style={styles.container}>
      <View
        style={[
          styles.qrFrame,
          {
            backgroundColor: theme.colors.surface,
            borderColor: theme.colors.border,
            borderRadius: theme.radii.lg,
          },
        ]}
      >
        <QRCode
          value={qrToken}
          size={size}
          color={theme.colors.text}
          backgroundColor={theme.colors.surface}
        />
      </View>
      <View style={styles.pinBlock}>
        <Text variant="small" style={{ color: theme.colors.textMuted }}>
          O comparte el código PIN
        </Text>
        <Text
          variant="h1"
          style={{
            color: theme.colors.primary,
            letterSpacing: 8,
            marginTop: 4,
          }}
        >
          {pickupCode}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', gap: 16 },
  qrFrame: { padding: 16, borderWidth: 1 },
  pinBlock: { alignItems: 'center' },
});
