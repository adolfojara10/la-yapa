import GorhomBottomSheet, {
  BottomSheetBackdrop,
  BottomSheetScrollView,
  BottomSheetView,
  type BottomSheetBackdropProps,
} from '@gorhom/bottom-sheet';
import {
  forwardRef,
  useCallback,
  useImperativeHandle,
  useMemo,
  useRef,
  type ReactNode,
} from 'react';

import { useTheme } from '@/theme';

export interface BottomSheetRef {
  open: () => void;
  close: () => void;
  snapTo: (index: number) => void;
}

export interface BottomSheetProps {
  children: ReactNode;
  snapPoints?: (string | number)[];
  scrollable?: boolean;
  enablePanDownToClose?: boolean;
  onChange?: (index: number) => void;
}

export const BottomSheet = forwardRef<BottomSheetRef, BottomSheetProps>(function BottomSheet(
  {
    children,
    snapPoints: snapPointsProp,
    scrollable = false,
    enablePanDownToClose = true,
    onChange,
  },
  ref,
) {
  const { theme } = useTheme();
  const sheetRef = useRef<GorhomBottomSheet>(null);

  const snapPoints = useMemo(() => snapPointsProp ?? ['50%', '90%'], [snapPointsProp]);

  useImperativeHandle(
    ref,
    () => ({
      open: () => sheetRef.current?.expand(),
      close: () => sheetRef.current?.close(),
      snapTo: (index) => sheetRef.current?.snapToIndex(index),
    }),
    [],
  );

  const renderBackdrop = useCallback(
    (props: BottomSheetBackdropProps) => (
      <BottomSheetBackdrop {...props} appearsOnIndex={0} disappearsOnIndex={-1} pressBehavior="close" />
    ),
    [],
  );

  const Inner = scrollable ? BottomSheetScrollView : BottomSheetView;

  return (
    <GorhomBottomSheet
      ref={sheetRef}
      index={-1} // start closed
      snapPoints={snapPoints}
      enablePanDownToClose={enablePanDownToClose}
      onChange={onChange}
      backdropComponent={renderBackdrop}
      backgroundStyle={{
        backgroundColor: theme.colors.surface,
        borderTopLeftRadius: theme.radii.xl,
        borderTopRightRadius: theme.radii.xl,
      }}
      handleIndicatorStyle={{ backgroundColor: theme.colors.borderStrong }}
    >
      <Inner style={{ flex: 1, padding: theme.spacing[5] }}>{children}</Inner>
    </GorhomBottomSheet>
  );
});
