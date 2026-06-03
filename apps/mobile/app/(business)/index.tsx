import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useAuthStore } from '@/auth/store';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';

export default function BusinessHome() {
  const { theme } = useTheme();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <View style={styles.body}>
        <Text variant="h1" style={{ color: theme.colors.primary }}>
          ¡Bienvenido!
        </Text>
        <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 8 }}>
          {user?.email}
        </Text>
        <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 16 }}>
          La onboarding de negocios (RUC, ubicación, primera bolsa) llega en la próxima sesión.
        </Text>
        <View style={{ marginTop: 24 }}>
          <Button variant="ghost" onPress={logout}>
            Cerrar sesión
          </Button>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, paddingHorizontal: 24 },
  body: { flex: 1, justifyContent: 'center' },
});
