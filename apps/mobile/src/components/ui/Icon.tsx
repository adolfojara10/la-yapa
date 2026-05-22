/**
 * Icon system.
 *
 * Convention: import any icon directly from `lucide-react-native`, but pass it
 * through this wrapper so the size and color follow theme defaults.
 *
 *   import { Heart } from 'lucide-react-native';
 *   <Icon icon={Heart} />              // theme-colored, default size
 *   <Icon icon={Heart} tone="error" size={28} />
 */
import type { LucideIcon } from 'lucide-react-native';

import { useTheme } from '@/theme';

export type IconTone =
  | 'text'
  | 'textMuted'
  | 'primary'
  | 'secondary'
  | 'success'
  | 'warning'
  | 'error'
  | 'info'
  | 'inverse';

export interface IconProps {
  icon: LucideIcon;
  size?: number;
  tone?: IconTone;
  strokeWidth?: number;
  color?: string;
}

export function Icon({ icon: Cmp, size = 20, tone = 'text', strokeWidth = 2, color }: IconProps) {
  const { theme } = useTheme();
  const tones: Record<IconTone, string> = {
    text: theme.colors.text,
    textMuted: theme.colors.textMuted,
    primary: theme.colors.primary,
    secondary: theme.colors.secondary,
    success: theme.colors.success,
    warning: theme.colors.warning,
    error: theme.colors.error,
    info: theme.colors.info,
    inverse: theme.colors.textInverse,
  };
  return <Cmp size={size} strokeWidth={strokeWidth} color={color ?? tones[tone]} />;
}
