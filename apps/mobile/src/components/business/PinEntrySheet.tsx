/**
 * Bottom sheet for manual PIN entry. Reuses the auth-flow OtpInput at
 * length=4 for the 4-digit pickup code.
 *
 * Location resolution: the sheet defaults to the location of the first
 * active order. With a single-location business this is correct and
 * invisible to the vendor. With multiple locations we'd need a picker;
 * for now we use the most-recent active order's location as a sensible
 * default and document the multi-location limitation in PROGRESS.md.
 */
import BottomSheet, { BottomSheetView } from '@gorhom/bottom-sheet';
import { forwardRef, useImperativeHandle, useMemo, useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { OtpInput } from '@/components/auth/OtpInput';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';

import type { BusinessOrder } from '@layapa/shared-types';

export interface PinSheetHandle {
  open: (orders: BusinessOrder[]) => void;
  close: () => void;
}

interface Props {
  onSubmit: (locationId: number, pin: string) => void | Promise<void>;
  submitting: boolean;
}

export const PinEntrySheet = forwardRef<PinSheetHandle, Props>(function PinEntrySheet(
  { onSubmit, submitting },
  ref,
) {
  const { theme } = useTheme();
  const sheetRef = useRef<BottomSheet>(null);
  const snapPoints = useMemo(() => ['55%'], []);
  const [pin, setPin] = useState('');
  const [locationId, setLocationId] = useState<number | null>(null);

  useImperativeHandle(ref, () => ({
    open: (orders) => {
      setPin('');
      // Default to the location of the first active order. If none,
      // location stays null and submit is disabled.
      setLocationId(orders[0]?.business_location_id ?? null);
      sheetRef.current?.snapToIndex(0);
    },
    close: () => sheetRef.current?.close(),
  }));

  function handleConfirm() {
    if (!locationId || pin.length !== 4) return;
    void onSubmit(locationId, pin);
  }

  return (
    <BottomSheet
      ref={sheetRef}
      index={-1}
      snapPoints={snapPoints}
      enablePanDownToClose
      backgroundStyle={{ backgroundColor: theme.colors.surface }}
      handleIndicatorStyle={{ backgroundColor: theme.colors.border }}
    >
      <BottomSheetView style={styles.content}>
        <Text variant="h3" style={{ color: theme.colors.text }}>
          Ingresar PIN
        </Text>
        <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
          Pide al cliente el código de 4 dígitos en su pantalla de pedido.
        </Text>

        <View style={styles.otpWrap}>
          <OtpInput
            value={pin}
            onChange={(next) => setPin(next.slice(0, 4))}
            length={4}
            onComplete={() => {}}
          />
        </View>

        <Button
          variant="primary"
          size="lg"
          fullWidth
          loading={submitting}
          disabled={pin.length !== 4 || locationId === null}
          onPress={handleConfirm}
        >
          Confirmar retiro
        </Button>

        {locationId === null ? (
          <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 12 }}>
            No tienes pedidos activos para confirmar.
          </Text>
        ) : null}
      </BottomSheetView>
    </BottomSheet>
  );
});

const styles = StyleSheet.create({
  content: { padding: 20, gap: 12 },
  otpWrap: { alignItems: 'center', marginVertical: 16 },
});
