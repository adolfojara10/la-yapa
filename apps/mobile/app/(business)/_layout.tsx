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
      <Stack.Screen name="onboarding" options={{ title: 'Onboarding negocio' }} />
      <Stack.Screen name="status" options={{ title: 'Estado de tu cuenta' }} />
      <Stack.Screen name="analytics" options={{ title: 'Analitica' }} />
      <Stack.Screen name="orders/index" options={{ title: 'Pedidos' }} />
      <Stack.Screen name="bags/new" options={{ title: 'Nueva bolsa' }} />
      <Stack.Screen name="bags/[id]" options={{ title: 'Editar bolsa' }} />
      <Stack.Screen name="locations" options={{ title: 'Ubicaciones' }} />
      <Stack.Screen name="orders/[id]" options={{ title: 'Pedido' }} />
      <Stack.Screen name="orders/scan" options={{ title: 'Escanear QR', presentation: 'modal' }} />
    </Stack>
  );
}
