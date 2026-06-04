/**
 * Live-updating countdown to pickup_window_start (before window opens) or
 * pickup_window_end (during window). Re-renders once per minute.
 */
import { useEffect, useState } from 'react';

import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';

interface Props {
  start: string;
  end: string;
}

function describe(now: Date, start: Date, end: Date): { text: string; urgent: boolean } {
  if (now >= end) return { text: 'Ventana cerrada', urgent: true };
  if (now < start) {
    const diffMin = Math.ceil((start.getTime() - now.getTime()) / 60_000);
    if (diffMin < 60) return { text: `Abre en ${diffMin} min`, urgent: false };
    const h = Math.floor(diffMin / 60);
    const m = diffMin % 60;
    return { text: `Abre en ${h}h ${m}min`, urgent: false };
  }
  const diffMin = Math.ceil((end.getTime() - now.getTime()) / 60_000);
  if (diffMin <= 15) return { text: `Cierra en ${diffMin} min`, urgent: true };
  if (diffMin < 60) return { text: `Cierra en ${diffMin} min`, urgent: false };
  const h = Math.floor(diffMin / 60);
  const m = diffMin % 60;
  return { text: `Cierra en ${h}h ${m}min`, urgent: false };
}

export function PickupCountdown({ start, end }: Props) {
  const { theme } = useTheme();
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(id);
  }, []);

  const { text, urgent } = describe(now, new Date(start), new Date(end));
  return (
    <Text
      variant="bodyStrong"
      style={{ color: urgent ? theme.colors.error : theme.colors.primary }}
    >
      {text}
    </Text>
  );
}
