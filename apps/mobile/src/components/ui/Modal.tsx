import { X } from 'lucide-react-native';
import type { ReactNode } from 'react';
import {
  Modal as RNModal,
  Pressable,
  StyleSheet,
  View,
  type ModalProps as RNModalProps,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/theme';

import { Text } from './Text';

export interface ModalProps extends Pick<RNModalProps, 'visible' | 'onRequestClose'> {
  title?: string;
  description?: string;
  children?: ReactNode;
  footer?: ReactNode;
  dismissOnBackdrop?: boolean;
}

export function Modal({
  visible,
  onRequestClose,
  title,
  description,
  children,
  footer,
  dismissOnBackdrop = true,
}: ModalProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  return (
    <RNModal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onRequestClose}
      statusBarTranslucent
    >
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Cerrar"
        style={[styles.backdrop, { backgroundColor: theme.colors.overlay }]}
        onPress={dismissOnBackdrop ? onRequestClose : undefined}
      >
        <Pressable
          onPress={(e) => e.stopPropagation()}
          style={[
            styles.sheet,
            {
              backgroundColor: theme.colors.surface,
              borderRadius: theme.radii.lg,
              padding: theme.spacing[5],
              marginHorizontal: theme.spacing[4],
              marginTop: insets.top + theme.spacing[6],
              marginBottom: insets.bottom + theme.spacing[6],
              maxWidth: 480,
              width: '100%',
            },
          ]}
        >
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Cerrar diálogo"
            onPress={onRequestClose}
            style={styles.close}
            hitSlop={8}
          >
            <X size={20} color={theme.colors.textMuted} />
          </Pressable>

          {title ? (
            <Text variant="h3" style={{ marginBottom: theme.spacing[2] }}>
              {title}
            </Text>
          ) : null}
          {description ? (
            <Text variant="small" color="textMuted" style={{ marginBottom: theme.spacing[4] }}>
              {description}
            </Text>
          ) : null}

          {children}

          {footer ? <View style={{ marginTop: theme.spacing[5] }}>{footer}</View> : null}
        </Pressable>
      </Pressable>
    </RNModal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sheet: {
    position: 'relative',
  },
  close: {
    position: 'absolute',
    top: 12,
    right: 12,
    zIndex: 1,
  },
});
