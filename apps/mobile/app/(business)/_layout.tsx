import { Stack } from 'expo-router';

import { useTheme } from '@/theme';

export default function BusinessLayout() {
  const { theme } = useTheme();
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: theme.colors.surface },
        headerTintColor: theme.colors.text,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="orders/[id]" options={{ title: 'Pedido' }} />
      <Stack.Screen name="orders/scan" options={{ title: 'Escanear QR', presentation: 'modal' }} />
    </Stack>
  );
}
