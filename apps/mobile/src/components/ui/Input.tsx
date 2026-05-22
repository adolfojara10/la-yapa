import { Eye, EyeOff, Search } from 'lucide-react-native';
import { forwardRef, useState, type ReactNode } from 'react';
import {
  Pressable,
  StyleSheet,
  TextInput,
  type TextInputProps,
  View,
} from 'react-native';

import { useTheme } from '@/theme';

import { Text } from './Text';

export type InputVariant = 'text' | 'password' | 'search';

export interface InputProps extends Omit<TextInputProps, 'style'> {
  label?: string;
  helperText?: string;
  errorText?: string;
  variant?: InputVariant;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

export const Input = forwardRef<TextInput, InputProps>(function Input(
  {
    label,
    helperText,
    errorText,
    variant = 'text',
    leftIcon,
    rightIcon,
    onFocus,
    onBlur,
    secureTextEntry,
    ...rest
  },
  ref,
) {
  const { theme } = useTheme();
  const [focused, setFocused] = useState(false);
  const [passwordHidden, setPasswordHidden] = useState(true);

  const isError = Boolean(errorText);
  const isPassword = variant === 'password';
  const showSecure = isPassword ? passwordHidden : secureTextEntry;

  const borderColor = isError
    ? theme.colors.error
    : focused
      ? theme.colors.focusRing
      : theme.colors.border;

  const resolvedLeftIcon =
    leftIcon ?? (variant === 'search' ? <Search size={18} color={theme.colors.textMuted} /> : null);

  const resolvedRightIcon = isPassword ? (
    <Pressable
      hitSlop={8}
      onPress={() => setPasswordHidden((p) => !p)}
      accessibilityRole="button"
      accessibilityLabel={passwordHidden ? 'Mostrar contraseña' : 'Ocultar contraseña'}
    >
      {passwordHidden ? (
        <Eye size={18} color={theme.colors.textMuted} />
      ) : (
        <EyeOff size={18} color={theme.colors.textMuted} />
      )}
    </Pressable>
  ) : (
    rightIcon ?? null
  );

  return (
    <View style={{ width: '100%' }}>
      {label ? (
        <Text variant="small" color="textMuted" style={{ marginBottom: theme.spacing[1] }}>
          {label}
        </Text>
      ) : null}

      <View
        style={[
          styles.row,
          {
            borderColor,
            borderWidth: 1,
            borderRadius: theme.radii.md,
            backgroundColor: theme.colors.surface,
            paddingHorizontal: theme.spacing[3],
            minHeight: 44,
          },
        ]}
      >
        {resolvedLeftIcon ? (
          <View style={{ marginRight: theme.spacing[2] }}>{resolvedLeftIcon}</View>
        ) : null}

        <TextInput
          ref={ref}
          secureTextEntry={showSecure}
          placeholderTextColor={theme.colors.textMuted}
          onFocus={(e) => {
            setFocused(true);
            onFocus?.(e);
          }}
          onBlur={(e) => {
            setFocused(false);
            onBlur?.(e);
          }}
          style={[
            styles.input,
            {
              color: theme.colors.text,
              fontFamily: theme.fonts.body,
              fontSize: theme.type.body.fontSize,
            },
          ]}
          {...rest}
        />

        {resolvedRightIcon ? (
          <View style={{ marginLeft: theme.spacing[2] }}>{resolvedRightIcon}</View>
        ) : null}
      </View>

      {errorText ? (
        <Text variant="caption" color="error" style={{ marginTop: theme.spacing[1] }}>
          {errorText}
        </Text>
      ) : helperText ? (
        <Text variant="caption" color="textMuted" style={{ marginTop: theme.spacing[1] }}>
          {helperText}
        </Text>
      ) : null}
    </View>
  );
});

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  input: {
    flex: 1,
    paddingVertical: 0, // RN Android adds default padding
  },
});
