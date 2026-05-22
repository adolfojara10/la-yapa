import type { ReactNode } from 'react';
import { View } from 'react-native';

import { useTheme } from '@/theme';

import { Text } from './Text';

export type BadgeTone = 'neutral' | 'primary' | 'success' | 'warning' | 'error' | 'info' | 'accent';

export interface BadgeProps {
  children: ReactNode;
  tone?: BadgeTone;
}

export function Badge({ children, tone = 'primary' }: BadgeProps) {
  const { theme } = useTheme();

  const styles: Record<BadgeTone, { bg: string; fg: string }> = {
    neutral: { bg: theme.colors.surfaceMuted, fg: theme.colors.textMuted },
    primary: { bg: theme.colors.primarySoft, fg: theme.colors.primary },
    success: { bg: theme.colors.successSoft, fg: theme.colors.success },
    warning: { bg: theme.colors.warningSoft, fg: theme.colors.warning },
    error: { bg: theme.colors.errorSoft, fg: theme.colors.error },
    info: { bg: theme.colors.infoSoft, fg: theme.colors.info },
    accent: { bg: theme.colors.accentSoft, fg: theme.colors.text },
  };

  const { bg, fg } = styles[tone];

  return (
    <View
      style={{
        alignSelf: 'flex-start',
        backgroundColor: bg,
        paddingHorizontal: theme.spacing[2],
        paddingVertical: theme.spacing[1],
        borderRadius: theme.radii.full,
      }}
    >
      <Text variant="caption" style={{ color: fg }}>
        {children}
      </Text>
    </View>
  );
}
