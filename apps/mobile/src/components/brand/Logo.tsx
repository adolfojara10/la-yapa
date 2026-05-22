import LogoColor from '@/assets/logo/logo-color.svg';
import LogoMark from '@/assets/logo/logo-mark.svg';
import LogoMonoDark from '@/assets/logo/logo-mono-dark.svg';
import LogoMonoWhite from '@/assets/logo/logo-mono-white.svg';
import { useTheme } from '@/theme';

export type LogoVariant = 'color' | 'mono-dark' | 'mono-white' | 'mark' | 'auto';

export interface LogoProps {
  variant?: LogoVariant;
  width?: number;
}

export function Logo({ variant = 'auto', width = 200 }: LogoProps) {
  const { mode } = useTheme();
  const resolved: Exclude<LogoVariant, 'auto'> =
    variant === 'auto' ? (mode === 'dark' ? 'mono-white' : 'color') : variant;

  switch (resolved) {
    case 'mark':
      return <LogoMark width={width} height={width} />;
    case 'mono-dark':
      return <LogoMonoDark width={width} height={Math.round(width * (100 / 360))} />;
    case 'mono-white':
      return <LogoMonoWhite width={width} height={Math.round(width * (100 / 360))} />;
    case 'color':
    default:
      return <LogoColor width={width} height={Math.round(width * (100 / 360))} />;
  }
}
