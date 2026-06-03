/**
 * 6-digit OTP input optimized for paste + autofill.
 *
 * Implementation note: under the hood this is a single hidden TextInput
 * sized to fill the row of "boxes" we draw on top. Trying to manage focus
 * across 6 native inputs is brittle on Android (different keyboard apps
 * fire onChangeText differently for autofilled codes); a single input
 * sidesteps the entire problem and Apple's `oneTimeCode` content type is
 * picked up automatically on iOS.
 */
import { useRef, useState } from 'react';
import {
  Platform,
  Pressable,
  StyleSheet,
  TextInput,
  type TextInputProps,
  View,
} from 'react-native';

import { useTheme } from '@/theme';

import { Text } from '../ui/Text';

interface OtpInputProps {
  value: string;
  onChange: (next: string) => void;
  length?: number;
  onComplete?: (code: string) => void;
  error?: string;
  autoFocus?: boolean;
}

export function OtpInput({
  value,
  onChange,
  length = 6,
  onComplete,
  error,
  autoFocus = true,
}: OtpInputProps) {
  const { theme } = useTheme();
  const [focused, setFocused] = useState(autoFocus);
  const ref = useRef<TextInput>(null);

  const cells = Array.from({ length }, (_, i) => value[i] ?? '');
  const activeIndex = Math.min(value.length, length - 1);

  const handleChange: TextInputProps['onChangeText'] = (next) => {
    const digits = next.replace(/\D/g, '').slice(0, length);
    onChange(digits);
    if (digits.length === length) onComplete?.(digits);
  };

  return (
    <Pressable
      onPress={() => ref.current?.focus()}
      style={styles.container}
      accessibilityRole="none"
    >
      <View style={styles.row}>
        {cells.map((digit, i) => {
          const isActive = focused && i === activeIndex;
          const borderColor = error
            ? theme.colors.error
            : isActive
              ? theme.colors.primary
              : theme.colors.border;
          return (
            <View
              key={i}
              style={[
                styles.cell,
                {
                  borderColor,
                  borderRadius: theme.radii.md,
                  backgroundColor: theme.colors.surface,
                },
              ]}
            >
              <Text variant="h3" style={{ color: theme.colors.text }}>
                {digit}
              </Text>
            </View>
          );
        })}
      </View>
      <TextInput
        ref={ref}
        value={value}
        onChangeText={handleChange}
        keyboardType="number-pad"
        maxLength={length}
        autoFocus={autoFocus}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        textContentType={Platform.OS === 'ios' ? 'oneTimeCode' : 'oneTimeCode'}
        autoComplete="sms-otp"
        importantForAutofill="yes"
        style={styles.hiddenInput}
        accessibilityLabel="Código de verificación"
      />
      {error ? (
        <Text variant="small" style={{ color: theme.colors.error, marginTop: theme.spacing[2] }}>
          {error}
        </Text>
      ) : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center' },
  row: { flexDirection: 'row', gap: 8 },
  cell: {
    width: 44,
    height: 56,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // The actual TextInput is offscreen but focusable.
  hiddenInput: {
    position: 'absolute',
    opacity: 0,
    width: 1,
    height: 1,
  },
});
