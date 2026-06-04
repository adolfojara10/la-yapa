/**
 * Bottom sheet that lists the bags at a selected map location.
 *
 * Exposes an imperative handle (expand/close) so the map view can drive
 * open/close in response to marker taps without prop-drilling boolean state.
 */
import BottomSheet, { BottomSheetFlatList } from '@gorhom/bottom-sheet';
import { useRouter } from 'expo-router';
import { forwardRef, useCallback, useImperativeHandle, useMemo, useRef } from 'react';
import { StyleSheet } from 'react-native';

import { useTheme } from '@/theme';

import { BagCard } from './BagCard';

import type { BagListItem } from '@layapa/shared-types';

export interface BottomSheetHandle {
  expand: () => void;
  close: () => void;
}

interface Props {
  bags: BagListItem[];
  onDismiss: () => void;
}

export const BagBottomSheet = forwardRef<BottomSheetHandle, Props>(function BagBottomSheet(
  { bags, onDismiss },
  ref,
) {
  const { theme } = useTheme();
  const router = useRouter();
  const sheetRef = useRef<BottomSheet>(null);
  const snapPoints = useMemo(() => ['40%', '85%'], []);

  useImperativeHandle(ref, () => ({
    expand: () => sheetRef.current?.snapToIndex(0),
    close: () => sheetRef.current?.close(),
  }));

  const handleChange = useCallback(
    (index: number) => {
      if (index === -1) onDismiss();
    },
    [onDismiss],
  );

  return (
    <BottomSheet
      ref={sheetRef}
      index={-1}
      snapPoints={snapPoints}
      enablePanDownToClose
      onChange={handleChange}
      backgroundStyle={{ backgroundColor: theme.colors.surface }}
      handleIndicatorStyle={{ backgroundColor: theme.colors.border }}
    >
      <BottomSheetFlatList<BagListItem>
        data={bags}
        keyExtractor={(b: BagListItem) => b.id}
        renderItem={({ item }: { item: BagListItem }) => (
          <BagCard
            bag={item}
            onPress={() => {
              sheetRef.current?.close();
              router.push(`/(consumer)/bag/${item.id}`);
            }}
          />
        )}
        contentContainerStyle={styles.list}
      />
    </BottomSheet>
  );
});

const styles = StyleSheet.create({
  list: { padding: 16, paddingBottom: 32 },
});
