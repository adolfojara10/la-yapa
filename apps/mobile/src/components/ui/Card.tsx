import type { ReactNode } from 'react';
import { View, type StyleProp, type ViewStyle } from 'react-native';

import { useTheme } from '@/theme';

export interface CardProps {
  children: ReactNode;
  padded?: boolean;
  elevated?: boolean;
  style?: StyleProp<ViewStyle>;
}

export function Card({ children, padded = true, elevated = true, style }: CardProps) {
  const { theme } = useTheme();
  const shadow = elevated ? theme.shadows.sm.rn : theme.shadows.none.rn;

  return (
    <View
      style={[
        {
          backgroundColor: theme.colors.surface,
          borderRadius: theme.radii.lg,
          borderColor: theme.colors.border,
          borderWidth: 1,
          padding: padded ? theme.spacing[4] : 0,
        },
        shadow,
        style,
      ]}
    >
      {children}
    </View>
  );
}
