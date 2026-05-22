import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react-native';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { Animated, Pressable, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/theme';

import { Text } from './Text';

export type ToastTone = 'success' | 'error' | 'warning' | 'info';

interface ToastOptions {
  title: string;
  description?: string;
  tone?: ToastTone;
  durationMs?: number;
}

interface ToastInstance extends Required<Omit<ToastOptions, 'description'>> {
  id: number;
  description?: string;
}

interface ToastContextValue {
  show: (opts: ToastOptions) => number;
  dismiss: (id: number) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastInstance[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((arr) => arr.filter((t) => t.id !== id));
  }, []);

  const show = useCallback(
    ({ title, description, tone = 'info', durationMs = 3500 }: ToastOptions) => {
      const id = ++nextId;
      setToasts((arr) => [...arr, { id, title, description, tone, durationMs }]);
      return id;
    },
    [],
  );

  const value = useMemo<ToastContextValue>(() => ({ show, dismiss }), [show, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}

// ---------- Internals ----------

function ToastViewport({
  toasts,
  onDismiss,
}: {
  toasts: ToastInstance[];
  onDismiss: (id: number) => void;
}) {
  const insets = useSafeAreaInsets();
  return (
    <View
      pointerEvents="box-none"
      style={[styles.viewport, { top: insets.top + 8 }]}
    >
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </View>
  );
}

function ToastItem({
  toast,
  onDismiss,
}: {
  toast: ToastInstance;
  onDismiss: (id: number) => void;
}) {
  const { theme } = useTheme();
  const opacity = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(-16)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration: theme.motion.duration.base,
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        toValue: 0,
        duration: theme.motion.duration.base,
        useNativeDriver: true,
      }),
    ]).start();

    const timer = setTimeout(() => onDismiss(toast.id), toast.durationMs);
    return () => clearTimeout(timer);
  }, [opacity, translateY, theme.motion.duration.base, onDismiss, toast.id, toast.durationMs]);

  const tones: Record<ToastTone, { bg: string; fg: string; icon: ReactNode }> = {
    success: {
      bg: theme.colors.successSoft,
      fg: theme.colors.success,
      icon: <CheckCircle2 size={20} color={theme.colors.success} />,
    },
    error: {
      bg: theme.colors.errorSoft,
      fg: theme.colors.error,
      icon: <XCircle size={20} color={theme.colors.error} />,
    },
    warning: {
      bg: theme.colors.warningSoft,
      fg: theme.colors.warning,
      icon: <AlertTriangle size={20} color={theme.colors.warning} />,
    },
    info: {
      bg: theme.colors.infoSoft,
      fg: theme.colors.info,
      icon: <Info size={20} color={theme.colors.info} />,
    },
  };
  const t = tones[toast.tone];

  return (
    <Animated.View
      style={[
        styles.toast,
        theme.shadows.md.rn,
        {
          backgroundColor: t.bg,
          borderColor: t.fg,
          borderRadius: theme.radii.md,
          padding: theme.spacing[3],
          opacity,
          transform: [{ translateY }],
        },
      ]}
    >
      <Pressable
        onPress={() => onDismiss(toast.id)}
        accessibilityRole="alert"
        accessibilityLabel={toast.title}
        style={styles.toastRow}
      >
        <View style={{ marginRight: theme.spacing[2] }}>{t.icon}</View>
        <View style={{ flex: 1 }}>
          <Text variant="bodyStrong" style={{ color: t.fg }}>
            {toast.title}
          </Text>
          {toast.description ? (
            <Text variant="small" style={{ color: t.fg, opacity: 0.85 }}>
              {toast.description}
            </Text>
          ) : null}
        </View>
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  viewport: {
    position: 'absolute',
    left: 16,
    right: 16,
    gap: 8,
    zIndex: 200,
  },
  toast: {
    borderWidth: 1,
  },
  toastRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
});
