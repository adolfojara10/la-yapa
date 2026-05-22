import type { TypeScaleToken } from '@layapa/ui';
import type { ReactNode } from 'react';
import {
  Text as RNText,
  type StyleProp,
  type TextProps as RNTextProps,
  type TextStyle,
} from 'react-native';

import { useTheme } from '@/theme';

export interface TextProps extends Omit<RNTextProps, 'style'> {
  variant?: TypeScaleToken;
  color?: 'text' | 'textMuted' | 'textInverse' | 'primary' | 'secondary' | 'error' | 'success';
  align?: TextStyle['textAlign'];
  style?: StyleProp<TextStyle>;
  children?: ReactNode;
}

/**
 * Themed Text. Resolves variant → fontSize/lineHeight/family/weight and
 * color token → actual color from the current scheme.
 */
export function Text({
  variant = 'body',
  color = 'text',
  align,
  style,
  children,
  ...rest
}: TextProps) {
  const { theme } = useTheme();
  const v = theme.type[variant];
  const colorMap = {
    text: theme.colors.text,
    textMuted: theme.colors.textMuted,
    textInverse: theme.colors.textInverse,
    primary: theme.colors.primary,
    secondary: theme.colors.secondary,
    error: theme.colors.error,
    success: theme.colors.success,
  };

  return (
    <RNText
      style={[
        {
          fontSize: v.fontSize,
          lineHeight: v.lineHeight,
          fontWeight: v.fontWeight as TextStyle['fontWeight'],
          fontFamily: v.fontFamily,
          color: colorMap[color],
          textAlign: align,
        },
        style,
      ]}
      {...rest}
    >
      {children}
    </RNText>
  );
}
