import { Stack } from 'expo-router';

import { useTheme } from '@/theme';

export default function ConsumerLayout() {
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
      <Stack.Screen name="bag/[id]" options={{ title: '', headerTransparent: true }} />
    </Stack>
  );
}
