import { forwardRef, type ReactNode } from 'react';
import {
  ActivityIndicator,
  Pressable,
  type PressableProps,
  StyleSheet,
  View,
} from 'react-native';

import { useTheme } from '@/theme';

import { Text } from './Text';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends Omit<PressableProps, 'children' | 'style'> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}

const SIZE = {
  sm: { height: 36, paddingX: 12, fontVariant: 'small' as const },
  md: { height: 44, paddingX: 16, fontVariant: 'bodyStrong' as const },
  lg: { height: 52, paddingX: 24, fontVariant: 'bodyStrong' as const },
};

export const Button = forwardRef<View, ButtonProps>(function Button(
  {
    children,
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled,
    leftIcon,
    rightIcon,
    fullWidth = false,
    ...rest
  },
  ref,
) {
  const { theme } = useTheme();
  const isDisabled = Boolean(disabled || loading);

  const palette = {
    primary: {
      bg: theme.colors.primary,
      bgPressed: theme.colors.primaryActive,
      fg: theme.colors.textOnPrimary,
      border: 'transparent',
    },
    secondary: {
      bg: theme.colors.secondary,
      bgPressed: theme.colors.secondaryHover,
      fg: theme.colors.textInverse,
      border: 'transparent',
    },
    ghost: {
      bg: 'transparent',
      bgPressed: theme.colors.surfaceMuted,
      fg: theme.colors.primary,
      border: theme.colors.border,
    },
    danger: {
      bg: theme.colors.error,
      bgPressed: theme.colors.error,
      fg: theme.colors.textInverse,
      border: 'transparent',
    },
  }[variant];

  const sz = SIZE[size];

  return (
    <Pressable
      ref={ref}
      accessibilityRole="button"
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.base,
        {
          height: sz.height,
          paddingHorizontal: sz.paddingX,
          borderRadius: theme.radii.md,
          backgroundColor: pressed && !isDisabled ? palette.bgPressed : palette.bg,
          borderColor: palette.border,
          borderWidth: variant === 'ghost' ? StyleSheet.hairlineWidth : 0,
          opacity: isDisabled ? 0.55 : 1,
          width: fullWidth ? '100%' : undefined,
        },
      ]}
      {...rest}
    >
      {loading ? (
        <ActivityIndicator color={palette.fg} />
      ) : (
        <>
          {leftIcon ? <View style={{ marginRight: theme.spacing[2] }}>{leftIcon}</View> : null}
          <Text variant={sz.fontVariant} style={{ color: palette.fg }}>
            {children}
          </Text>
          {rightIcon ? <View style={{ marginLeft: theme.spacing[2] }}>{rightIcon}</View> : null}
        </>
      )}
    </Pressable>
  );
});

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
